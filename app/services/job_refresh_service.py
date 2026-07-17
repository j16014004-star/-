"""新简历与周期性岗位推荐刷新。"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session, engine
from app.crud.job_recommendation import get_latest_login_session, get_latest_recommend_task
from app.models.job import JobRecommendTask
from app.models.resume import Resume
from app.services.recommendation_start_service import (
    RecommendationStartError,
    ensure_recommendation_task,
    is_login_state_ready,
)

logger = logging.getLogger(__name__)


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def trigger_refresh_for_new_resume(
    db: AsyncSession,
    *,
    user_id: int,
    resume: Resume,
) -> dict:
    """新简历解析完成后，复用最近选择和有效登录态启动一次全新采集。"""
    previous = await get_latest_recommend_task(db, user_id, "58")
    now = utc_now_naive()
    await db.execute(
        update(JobRecommendTask)
        .where(
            JobRecommendTask.user_id == user_id,
            JobRecommendTask.source == "58",
            JobRecommendTask.resume_id != resume.id,
            JobRecommendTask.status.in_(("pending", "crawling", "matching")),
        )
        .values(
            status="failed",
            progress=100,
            failure_code="superseded_by_new_resume",
            error_message="用户上传了新简历，本任务已停止并切换为新简历重新推荐",
            finished_at=now,
        )
    )
    await db.flush()

    session = await get_latest_login_session(db, user_id, "58")
    if not session:
        return {"status": "need_login", "task_id": None, "message": "新简历已生效；进入岗位推荐并登录58同城后将拉取最新岗位"}
    if not is_login_state_ready(session):
        if session.status == "logged_in":
            session.status = "expired"
            session.storage_state_ref = None
            session.error_message = "58同城登录态已失效，请重新登录后更新新简历的岗位推荐"
            await db.flush()
        return {"status": "need_login", "task_id": None, "message": session.error_message or "58同城登录态已失效，请重新登录"}

    try:
        result = await ensure_recommendation_task(
            db,
            user_id=user_id,
            resume_id=resume.id,
            source="58",
            login_session_id=session.id,
            limit=previous.requested_limit if previous else 20,
            target_role=previous.target_role if previous else None,
            target_city=previous.target_city if previous else None,
            resume_source="original",
            resume_optimization_id=None,
        )
    except RecommendationStartError as exc:
        return {"status": "pending", "task_id": None, "message": f"新简历已生效，岗位推荐将在当前任务完成后更新：{exc.message}"}
    return {"status": result.task.status, "task_id": result.task.id, "message": "新简历已生效，正在重新抓取并更新岗位推荐"}


async def run_periodic_job_refresh() -> int:
    """刷新超过配置周期的用户最新推荐；MySQL 锁避免多进程重复调度。"""
    async with engine.connect() as lock_connection:
        locked = await lock_connection.scalar(text("SELECT GET_LOCK('job_periodic_refresh', 0)"))
        if locked != 1:
            return 0
        try:
            async with async_session() as db:
                created = 0
                cutoff = utc_now_naive() - timedelta(hours=max(1, settings.CRAWL_INTERVAL_HOURS))
                tasks = list((await db.scalars(
                    select(JobRecommendTask)
                    .order_by(JobRecommendTask.created_at.desc())
                    .limit(2000)
                )).all())
                seen: set[tuple[int, str]] = set()
                for previous in tasks:
                    key = (previous.user_id, previous.source)
                    if key in seen:
                        continue
                    seen.add(key)
                    created_at = previous.created_at
                    if created_at.tzinfo is not None:
                        created_at = created_at.astimezone(timezone.utc).replace(tzinfo=None)
                    if previous.status not in ("success", "no_results") or created_at > cutoff:
                        continue
                    session = await get_latest_login_session(db, previous.user_id, previous.source)
                    if not session or not is_login_state_ready(session):
                        if session and session.status == "logged_in":
                            session.status = "expired"
                            session.storage_state_ref = None
                            session.error_message = "58同城登录态已失效，请重新登录以继续定时更新岗位"
                        continue
                    try:
                        result = await ensure_recommendation_task(
                            db,
                            user_id=previous.user_id,
                            resume_id=previous.resume_id,
                            source=previous.source,
                            login_session_id=session.id,
                            limit=previous.requested_limit,
                            target_role=previous.target_role,
                            target_city=previous.target_city,
                            resume_source=previous.resume_source,
                            resume_optimization_id=previous.resume_optimization_id,
                        )
                    except RecommendationStartError:
                        continue
                    if result.created:
                        created += 1
                        await db.commit()
                await db.commit()
                return created
        finally:
            await lock_connection.execute(text("SELECT RELEASE_LOCK('job_periodic_refresh')"))


async def job_refresh_scheduler() -> None:
    """应用内轻量调度循环；真正采集仍由独立 recommendation worker 执行。"""
    await asyncio.sleep(60)
    check_seconds = max(60, settings.JOB_REFRESH_CHECK_MINUTES * 60)
    while True:
        try:
            await run_periodic_job_refresh()
        except asyncio.CancelledError:
            raise
        except Exception:
            # 单次调度失败不能使 API 服务退出，下个周期会自动重试。
            logger.exception("周期性岗位推荐刷新失败")
        await asyncio.sleep(check_seconds)
