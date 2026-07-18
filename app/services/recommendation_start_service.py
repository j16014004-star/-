"""推荐任务启动编排服务。"""
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.job_recommendation import (
    create_recommend_task,
    get_active_recommend_task,
    get_latest_recommend_task_by_login_session,
    get_login_session,
)
from app.crud.resume import get_resume_by_id
from app.crud.resume_optimization import get_owned_saved_optimization_version
from app.models.job import JobPlatformLoginSession, JobRecommendTask
from app.models.user import User
from app.services.job_recommendation_rules import (
    build_search_keywords,
    infer_target_city,
    infer_target_role,
    normalize_city,
)
from app.services.skills_service import get_resume_skills
from app.services.platform_session_service import is_plausible_storage_state
from app.workers.process_launcher import WorkerLaunchError, launch_recommendation_worker


ACTIVE_TASK_STATUSES = ("pending", "crawling", "matching")


class RecommendationStartError(Exception):
    """业务可预期的推荐启动失败。"""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class RecommendationTaskStartResult:
    task: JobRecommendTask
    created: bool
    launched: bool


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def is_active_task(task: JobRecommendTask | None) -> bool:
    return bool(task and task.status in ACTIVE_TASK_STATUSES)


def is_stale_active_task(task: JobRecommendTask | None) -> bool:
    if not is_active_task(task):
        return False
    anchor = (
        getattr(task, "started_at", None)
        or getattr(task, "updated_at", None)
        or getattr(task, "created_at", None)
    )
    if not anchor:
        return False
    timeout = max(120, int(settings.WORKER_TASK_TIMEOUT_SECONDS) + 60)
    return (utc_now_naive() - to_naive_utc(anchor)).total_seconds() >= timeout


async def expire_stale_active_task(db: AsyncSession, task: JobRecommendTask | None) -> None:
    if not is_stale_active_task(task):
        return
    task.status = "failed"
    task.progress = 100
    task.failure_code = "worker_timeout"
    task.error_message = "上一次岗位抓取任务执行超时，已允许重新创建任务"
    task.finished_at = utc_now_naive()
    await db.flush()


def task_uses_selection(
    task: JobRecommendTask,
    resume_id: int,
    resume_source: str,
    resume_optimization_id: int | None,
) -> bool:
    return (
        task.resume_id == resume_id
        and task.resume_source == resume_source
        and task.resume_optimization_id == resume_optimization_id
    )


def is_login_state_ready(session: JobPlatformLoginSession) -> bool:
    now = utc_now_naive()
    if session.status != "logged_in" or session.expires_at < now:
        return False
    if not session.storage_state_ref:
        return False
    return is_plausible_storage_state(session.storage_state_ref, session.source)


async def ensure_recommendation_task(
    db: AsyncSession,
    *,
    user_id: int,
    resume_id: int,
    source: str,
    login_session_id: str,
    limit: int = 20,
    target_role: str | None = None,
    target_city: str | None = None,
    resume_source: str = "original",
    resume_optimization_id: int | None = None,
    launch_if_ready: bool = True,
    force_refresh: bool = False,
) -> RecommendationTaskStartResult:
    """确保当前用户在该平台有一个推荐任务，并在登录态可用时启动 worker。"""
    # 串行化同一用户的启动请求，避免前端重复点击创建多个活动任务。
    await db.execute(select(User.id).where(User.id == user_id).with_for_update())
    session = await get_login_session(db, login_session_id, user_id)
    if not session or session.source != source:
        raise RecommendationStartError("登录会话不存在或不属于当前平台", 409)

    # 网络重试或连续点击必须复用正在运行的任务，不能把健康任务改成失败。
    # 用户锁保证并发请求串行化，第二个请求会在这里看到第一个活动任务。
    session_task = await get_latest_recommend_task_by_login_session(db, login_session_id, user_id)
    await expire_stale_active_task(db, session_task)
    if is_active_task(session_task):
        if not task_uses_selection(session_task, resume_id, resume_source, resume_optimization_id):
            raise RecommendationStartError(
                "该登录会话已有其他简历的推荐任务正在执行，请等待完成后重试", 409,
            )
        launched = await launch_task_if_ready(db, session, session_task, launch_if_ready)
        return RecommendationTaskStartResult(session_task, created=False, launched=launched)

    active = await get_active_recommend_task(db, user_id, source)
    await expire_stale_active_task(db, active)
    if is_active_task(active):
        if not task_uses_selection(active, resume_id, resume_source, resume_optimization_id):
            raise RecommendationStartError(
                "当前平台已有其他简历的推荐任务正在执行，请等待完成后重试", 409,
            )
        launched = False
        if active.login_session_id == session.id:
            launched = await launch_task_if_ready(db, session, active, launch_if_ready)
        return RecommendationTaskStartResult(active, created=False, launched=launched)

    resume = await get_resume_by_id(db, resume_id, user_id)
    if not resume or resume.status != "completed":
        raise RecommendationStartError("简历不存在、无权访问或尚未处理完成", 404)

    selected_text = resume.extracted_text
    selected_structured_data = resume.structured_data
    optimized_version = None
    if resume_source == "optimized":
        if resume_optimization_id is None:
            raise RecommendationStartError("选择优化简历时必须提交优化简历版本", 422)
        optimized_version = await get_owned_saved_optimization_version(
            db, optimization_id=resume_optimization_id, user_id=user_id,
        )
        if not optimized_version or optimized_version.resume_id != resume_id:
            raise RecommendationStartError("优化简历不存在、未保存或不属于当前原始简历", 404)
        selected_text = optimized_version.optimized_content
        selected_structured_data = None
    elif resume_source != "original" or resume_optimization_id is not None:
        raise RecommendationStartError("简历来源参数无效", 422)

    skills = get_resume_skills(selected_structured_data, selected_text)
    if not skills:
        raise RecommendationStartError("简历未解析出可用于推荐的技能或岗位关键词", 422)

    resolved_role = (
        " ".join(target_role.split()).strip() if target_role else None
    ) or (optimized_version.target_role if optimized_version else None) or infer_target_role(
        selected_structured_data, selected_text, skills,
    )
    normalized_selected_city = normalize_city(target_city)
    if target_city and not normalized_selected_city:
        raise RecommendationStartError("当前暂不支持所选城市，请从城市下拉列表中选择", 422)
    resolved_city = normalized_selected_city or infer_target_city(
        resume.structured_data, resume.extracted_text,
    )
    keywords = build_search_keywords(resolved_role, skills)
    if not keywords:
        raise RecommendationStartError("无法生成有效的岗位搜索词，请明确选择目标岗位", 422)

    safe_limit = max(1, min(limit, 50))
    task = JobRecommendTask(
        id=str(uuid4()),
        user_id=user_id,
        resume_id=resume_id,
        resume_source=resume_source,
        resume_optimization_id=resume_optimization_id,
        login_session_id=session.id,
        source=source,
        target_role=resolved_role,
        target_city=resolved_city,
        extracted_skills=skills,
        search_keywords=keywords,
        requested_limit=safe_limit,
    )
    await create_recommend_task(db, task)
    launched = await launch_task_if_ready(db, session, task, launch_if_ready)
    return RecommendationTaskStartResult(task, created=True, launched=launched)


async def launch_task_if_ready(
    db: AsyncSession,
    session: JobPlatformLoginSession,
    task: JobRecommendTask,
    launch_if_ready: bool,
) -> bool:
    if not launch_if_ready or task.status != "pending":
        return False
    if task.started_at is not None:
        elapsed = (utc_now_naive() - to_naive_utc(task.started_at)).total_seconds()
        if elapsed < 60:
            return False
    if not is_login_state_ready(session):
        return False

    now = utc_now_naive()
    task.started_at = now
    session.consumed_at = now
    await db.flush()
    try:
        launch_recommendation_worker(task.id)
    except WorkerLaunchError as exc:
        task.status = "failed"
        task.progress = 100
        task.error_message = "无法启动推荐任务 worker，请稍后重试"
        task.finished_at = utc_now_naive()
        await db.flush()
        raise RecommendationStartError(task.error_message, 503) from exc
    return True


async def mark_login_pending_task_need_login(
    db: AsyncSession,
    *,
    user_id: int,
    login_session_id: str,
    message: str,
) -> None:
    task = await get_latest_recommend_task_by_login_session(db, login_session_id, user_id)
    if task and task.status == "pending":
        task.status = "need_login"
        task.progress = 100
        task.error_message = message
        task.finished_at = utc_now_naive()
        await db.flush()
