"""推荐任务启动编排服务。"""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.job_recommendation import (
    create_recommend_task,
    get_active_recommend_task,
    get_latest_recommend_task_by_login_session,
    get_login_session,
)
from app.crud.resume import get_resume_by_id
from app.models.job import JobPlatformLoginSession, JobRecommendTask
from app.services.skills_service import get_resume_skills
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


def is_login_state_ready(session: JobPlatformLoginSession) -> bool:
    now = utc_now_naive()
    if session.status != "logged_in" or session.expires_at < now:
        return False
    if not session.storage_state_ref:
        return False
    return Path(session.storage_state_ref).is_file()


async def ensure_recommendation_task(
    db: AsyncSession,
    *,
    user_id: int,
    resume_id: int,
    source: str,
    login_session_id: str,
    limit: int = 20,
    launch_if_ready: bool = True,
) -> RecommendationTaskStartResult:
    """确保当前用户在该平台有一个推荐任务，并在登录态可用时启动 worker。"""
    session = await get_login_session(db, login_session_id, user_id)
    if not session or session.source != source:
        raise RecommendationStartError("登录会话不存在或不属于当前平台", 409)

    session_task = await get_latest_recommend_task_by_login_session(db, login_session_id, user_id)
    if is_active_task(session_task):
        launched = await launch_task_if_ready(db, session, session_task, launch_if_ready)
        return RecommendationTaskStartResult(session_task, created=False, launched=launched)

    active = await get_active_recommend_task(db, user_id, source)
    if active:
        launched = False
        if active.login_session_id == session.id:
            launched = await launch_task_if_ready(db, session, active, launch_if_ready)
        return RecommendationTaskStartResult(active, created=False, launched=launched)

    resume = await get_resume_by_id(db, resume_id, user_id)
    if not resume or resume.status != "completed":
        raise RecommendationStartError("简历不存在、无权访问或尚未处理完成", 404)

    skills = get_resume_skills(resume.structured_data, resume.extracted_text)
    if not skills:
        raise RecommendationStartError("简历未解析出可用于推荐的技能或岗位关键词", 422)

    safe_limit = max(1, min(limit, 50))
    task = JobRecommendTask(
        id=str(uuid4()),
        user_id=user_id,
        resume_id=resume_id,
        login_session_id=session.id,
        source=source,
        extracted_skills=skills,
        search_keywords=skills[:5],
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
