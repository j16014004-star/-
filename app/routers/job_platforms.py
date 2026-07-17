"""招聘平台登录与任务化岗位推荐路由。"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.crud.job_recommendation import (
    create_login_session,
    get_latest_login_session,
    get_latest_recommend_task,
    get_latest_recommend_task_by_login_session,
    get_login_session,
    get_recommend_task,
    get_task_results,
)
from app.crud.resume import get_resume_by_id
from app.models.job import JobPlatformLoginSession, JobRecommendTask
from app.models.user import User
from app.schemas.job_recommendation import PlatformLoginStartRequest, RecommendTaskStartRequest
from app.services.recommendation_start_service import (
    RecommendationStartError,
    RecommendationTaskStartResult,
    ensure_recommendation_task,
    mark_login_pending_task_need_login,
)
from app.services.platform_session_service import is_plausible_storage_state, secure_state_path
from app.workers.process_launcher import WorkerLaunchError, launch_login_worker

router = APIRouter(tags=["岗位平台与推荐"])
PLATFORM_58 = {"source": "58", "name": "58同城", "enabled": True, "login_required": True}
LOGIN_URL_58 = "https://passport.58.com/login"


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_state_path(user_id: int, source: str) -> Path:
    return secure_state_path(user_id, source)


def sync_saved_login_state(session: JobPlatformLoginSession, user_id: int, source: str) -> bool:
    state_path = get_state_path(user_id, source)
    if not is_plausible_storage_state(state_path, source):
        return False
    session.status = "logged_in"
    session.storage_state_ref = str(state_path)
    session.error_message = None
    if session.expires_at <= utc_now_naive():
        session.expires_at = utc_now_naive() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return True
def task_brief(task: JobRecommendTask | None) -> dict:
    return {
        "recommend_task_id": task.id if task else None,
        "recommend_status": task.status if task else None,
        "recommend_poll_after_seconds": 2 if task else None,
    }


def raise_recommendation_start_error(exc: RecommendationStartError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


def build_login_response(
    session: JobPlatformLoginSession,
    message: str,
    task: JobRecommendTask | None = None,
) -> dict:
    return {
        "code": 200,
        "message": message,
        "data": {
            "login_session_id": session.id,
            "source": session.source,
            "source_name": "58同城",
            "status": session.status,
            "login_mode": (
                "remote_browser"
                if settings.PLAYWRIGHT_CDP_ENDPOINT.strip()
                else "server_browser"
            ),
            "login_url": LOGIN_URL_58,
            "browser_url": settings.PLAYWRIGHT_REMOTE_VIEW_URL.strip() or None,
            "expires_at": session.expires_at,
            "error_message": session.error_message,
            **task_brief(task),
            "poll_after_seconds": 2,
        },
    }


async def ensure_task_or_http(
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
    try:
        return await ensure_recommendation_task(
            db,
            user_id=user_id,
            resume_id=resume_id,
            source=source,
            login_session_id=login_session_id,
            limit=limit,
            target_role=target_role,
            target_city=target_city,
            resume_source=resume_source,
            resume_optimization_id=resume_optimization_id,
            launch_if_ready=launch_if_ready,
            force_refresh=force_refresh,
        )
    except RecommendationStartError as exc:
        raise_recommendation_start_error(exc)


def build_recommend_response(task: JobRecommendTask, message: str) -> dict:
    return {
        "code": 200,
        "message": message,
        "data": {
            "task_id": task.id,
            "status": task.status,
            "resume_id": task.resume_id,
            "resume_source": task.resume_source,
            "resume_optimization_id": task.resume_optimization_id,
            "source": task.source,
            "source_name": "58同城",
            "target_role": task.target_role,
            "target_city": task.target_city,
            "extracted_skills": task.extracted_skills or [],
            "search_keywords": task.search_keywords or [],
            "poll_after_seconds": 2,
        },
    }


async def try_ensure_task_for_status(
    db: AsyncSession,
    *,
    session: JobPlatformLoginSession,
    user_id: int,
    limit: int = 20,
) -> JobRecommendTask | None:
    task = await get_latest_recommend_task_by_login_session(db, session.id, user_id)
    if task and task.status != "pending":
        return task
    try:
        result = await ensure_recommendation_task(
            db,
            user_id=user_id,
            resume_id=session.resume_id,
            resume_source=session.resume_source,
            resume_optimization_id=session.resume_optimization_id,
            source=session.source,
            login_session_id=session.id,
            limit=limit,
        )
        return result.task
    except RecommendationStartError as exc:
        if session.status == "logged_in":
            session.error_message = f"自动推荐启动失败：{exc.message}"
            await db.flush()
        return None


@router.get("/api/job-platforms")
async def list_platforms(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    session = await get_latest_login_session(db, current_user.id, "58")
    status = "not_logged_in"
    if session:
        now = utc_now_naive()
        if sync_saved_login_state(session, current_user.id, "58"):
            status = session.status
            await db.flush()
        elif session.expires_at < now:
            status = "expired"
        elif session.status == "logged_in":
            session.status = "expired"
            session.storage_state_ref = None
            session.error_message = "登录态文件无效或认证 Cookie 已过期，请重新登录"
            status = "expired"
            await db.flush()
        else:
            status = session.status
            await db.flush()
    return {"code": 200, "message": "success", "data": {"items": [{**PLATFORM_58, "login_status": status}]}}


@router.post("/api/job-platforms/login/start")
async def start_login(body: PlatformLoginStartRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    resume = await get_resume_by_id(db, body.resume_id, current_user.id)
    if not resume or resume.status != "completed":
        raise HTTPException(status_code=404, detail="简历不存在、无权访问或尚未处理完成")

    now = utc_now_naive()
    latest = await get_latest_login_session(db, current_user.id, body.source)
    if latest:
        if sync_saved_login_state(latest, current_user.id, body.source):
            latest.resume_id = body.resume_id
            latest.resume_source = body.resume_source
            latest.resume_optimization_id = body.resume_optimization_id
            task_result = await ensure_task_or_http(
                db,
                user_id=current_user.id,
                resume_id=body.resume_id,
                source=body.source,
                login_session_id=latest.id,
                limit=body.limit,
                target_role=body.target_role,
                target_city=body.target_city,
                resume_source=body.resume_source,
                resume_optimization_id=body.resume_optimization_id,
                force_refresh=body.force_refresh,
            )
            await db.flush()
            return build_login_response(latest, "已检测到本地登录态，已开始拉取推荐岗位", task_result.task)
        if latest.expires_at >= now and latest.status == "waiting_login":
            if (
                latest.resume_id != body.resume_id
                or latest.resume_source != body.resume_source
                or latest.resume_optimization_id != body.resume_optimization_id
            ):
                latest.status = "expired"
                latest.error_message = "用户切换了简历，旧登录会话已取消"
                await mark_login_pending_task_need_login(
                    db,
                    user_id=current_user.id,
                    login_session_id=latest.id,
                    message=latest.error_message,
                )
            else:
                task_result = await ensure_task_or_http(
                    db,
                    user_id=current_user.id,
                    resume_id=body.resume_id,
                    source=body.source,
                    login_session_id=latest.id,
                    limit=body.limit,
                    target_role=body.target_role,
                    target_city=body.target_city,
                    resume_source=body.resume_source,
                    resume_optimization_id=body.resume_optimization_id,
                    launch_if_ready=False,
                    force_refresh=body.force_refresh,
                )
                await db.flush()
                return build_login_response(latest, "已存在进行中的登录窗口，请在该窗口中完成扫码登录", task_result.task)
        if latest.status == "logged_in":
            latest.status = "expired"
            latest.error_message = "登录态文件不存在或已失效，请重新登录"
            await mark_login_pending_task_need_login(
                db,
                user_id=current_user.id,
                login_session_id=latest.id,
                message=latest.error_message,
            )
            await db.flush()

    session_id = str(uuid4())
    expires_at = now + timedelta(seconds=settings.PLATFORM_LOGIN_TIMEOUT_SECONDS)
    session = JobPlatformLoginSession(
        id=session_id,
        user_id=current_user.id,
        resume_id=body.resume_id,
        resume_source=body.resume_source,
        resume_optimization_id=body.resume_optimization_id,
        source=body.source,
        expires_at=expires_at,
    )
    if sync_saved_login_state(session, current_user.id, body.source):
        await create_login_session(db, session)
        task_result = await ensure_task_or_http(
            db,
            user_id=current_user.id,
            resume_id=body.resume_id,
            source=body.source,
            login_session_id=session.id,
            limit=body.limit,
            target_role=body.target_role,
            target_city=body.target_city,
            resume_source=body.resume_source,
            resume_optimization_id=body.resume_optimization_id,
            force_refresh=body.force_refresh,
        )
        return build_login_response(session, "已检测到本地登录态，已开始拉取推荐岗位", task_result.task)

    await create_login_session(db, session)
    task_result = await ensure_task_or_http(
        db,
        user_id=current_user.id,
        resume_id=body.resume_id,
        source=body.source,
        login_session_id=session.id,
        limit=body.limit,
        target_role=body.target_role,
        target_city=body.target_city,
        resume_source=body.resume_source,
        resume_optimization_id=body.resume_optimization_id,
        launch_if_ready=False,
        force_refresh=body.force_refresh,
    )
    try:
        launch_login_worker(session_id)
    except WorkerLaunchError:
        session.status = "failed"
        session.error_message = "无法启动登录 worker，请确认浏览器与队列配置可用"
        await mark_login_pending_task_need_login(
            db,
            user_id=current_user.id,
            login_session_id=session.id,
            message=session.error_message,
        )
        await db.flush()
        raise HTTPException(status_code=503, detail=session.error_message)
    return build_login_response(session, "请在打开的浏览器中自行完成扫码登录，登录成功后会自动开始推荐", task_result.task)


@router.get("/api/job-platforms/login/{login_session_id}")
async def get_login_status(login_session_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    session = await get_login_session(db, login_session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="登录会话不存在")
    now = utc_now_naive()
    task = None
    if sync_saved_login_state(session, current_user.id, session.source):
        task = await try_ensure_task_for_status(db, session=session, user_id=current_user.id)
    elif session.status == "waiting_login" and session.expires_at < now:
        session.status = "expired"
        session.error_message = "登录超时，请重新发起登录"
        await mark_login_pending_task_need_login(
            db,
            user_id=current_user.id,
            login_session_id=session.id,
            message=session.error_message,
        )
    elif session.status == "waiting_login":
        task = await try_ensure_task_for_status(db, session=session, user_id=current_user.id)
    elif session.status == "logged_in":
        session.status = "expired"
        session.error_message = "登录态文件不存在或已失效，请重新登录"
        await mark_login_pending_task_need_login(
            db,
            user_id=current_user.id,
            login_session_id=session.id,
            message=session.error_message,
        )
    await db.flush()
    return build_login_response(session, "success", task)


@router.post("/api/jobs/recommend/start", status_code=202)
async def start_recommend_task(body: RecommendTaskStartRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    session = await get_login_session(db, body.login_session_id, current_user.id)
    now = utc_now_naive()
    if session:
        sync_saved_login_state(session, current_user.id, body.source)
        await db.flush()
    if (
        not session
        or session.source != body.source
        or session.status != "logged_in"
        or session.expires_at < now
        or not session.storage_state_ref
        or not is_plausible_storage_state(session.storage_state_ref, session.source)
    ):
        raise HTTPException(status_code=409, detail="登录会话已失效，请重新登录")
    task_result = await ensure_task_or_http(
        db,
        user_id=current_user.id,
        resume_id=body.resume_id,
        source=body.source,
        login_session_id=session.id,
        limit=body.limit,
        target_role=body.target_role,
        target_city=body.target_city,
        resume_source=body.resume_source,
        resume_optimization_id=body.resume_optimization_id,
        force_refresh=body.force_refresh,
    )
    task = task_result.task
    message = "推荐任务已创建" if task_result.created else "已有进行中的推荐任务"
    return build_recommend_response(task, message)


@router.get("/api/jobs/recommend/current")
async def get_current_recommend_task(
    resume_id: int | None = Query(default=None, gt=0),
    resume_source: str = Query(default="original", pattern="^(original|optimized)$"),
    resume_optimization_id: int | None = Query(default=None, gt=0),
    source: str = Query(default="58", pattern="^58$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """恢复当前正在执行或最近一次岗位推荐任务。"""
    if resume_id is not None:
        resume = await get_resume_by_id(db, resume_id, current_user.id)
        if not resume:
            raise HTTPException(status_code=404, detail="简历不存在或无权访问")
    if resume_source == "optimized" and resume_optimization_id is None:
        raise HTTPException(status_code=422, detail="选择优化简历时必须提交 resume_optimization_id")
    if resume_source == "original" and resume_optimization_id is not None:
        raise HTTPException(status_code=422, detail="原始简历不能提交 resume_optimization_id")
    task = await get_latest_recommend_task(
        db, current_user.id, source, resume_id, resume_source, resume_optimization_id,
    )
    return {
        "code": 200,
        "message": "success",
        "data": {"task": task_status_dict(task) if task else None},
    }


@router.get("/api/jobs/recommend/tasks/{task_id}")
async def get_task_status(task_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    task = await get_recommend_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="推荐任务不存在")
    return {"code": 200, "message": "success", "data": task_status_dict(task)}


@router.get("/api/jobs/recommend/tasks/{task_id}/results")
async def get_task_result_list(task_id: str, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    task = await get_recommend_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="推荐任务不存在")
    if task.status == "no_results":
        return {"code": 200, "message": "success", "data": {"task_id": task.id, "resume_id": task.resume_id, "resume_source": task.resume_source, "resume_optimization_id": task.resume_optimization_id, "source": task.source, "source_name": "58同城", "target_role": task.target_role, "target_city": task.target_city, "extracted_skills": task.extracted_skills or [], "search_keywords": task.search_keywords or [], "items": [], "total": 0, "page": page, "page_size": page_size}}
    if task.status != "success":
        raise HTTPException(status_code=409, detail="推荐任务尚未完成" if task.status not in ("need_login", "failed") else (task.error_message or "推荐任务未成功"))
    rows, total = await get_task_results(db, task.id, current_user.id, page, page_size)
    items = [{"id": job.id, "company": job.company, "company_logo": job.company_logo, "title": job.title, "salary_min": job.salary_min, "salary_max": job.salary_max, "city": job.city, "experience_required": job.experience_required, "education_required": job.education_required, "skills": job.skills or [], "match_score": rec.match_score, "matched_skills": rec.matched_skills or [], "match_reasons": rec.match_reasons or [], "source": job.source, "source_name": job.source_name, "source_url": job.source_url, "crawl_time": job.crawl_time} for rec, job in rows]
    return {"code": 200, "message": "success", "data": {"task_id": task.id, "resume_id": task.resume_id, "resume_source": task.resume_source, "resume_optimization_id": task.resume_optimization_id, "source": task.source, "source_name": "58同城", "target_role": task.target_role, "target_city": task.target_city, "extracted_skills": task.extracted_skills or [], "search_keywords": task.search_keywords or [], "items": items, "total": total, "page": page, "page_size": page_size}}


def task_status_dict(task: JobRecommendTask) -> dict:
    return {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "source": task.source,
        "source_name": "58同城",
        "resume_id": task.resume_id,
        "resume_source": task.resume_source,
        "resume_optimization_id": task.resume_optimization_id,
        "target_role": task.target_role,
        "target_city": task.target_city,
        "extracted_skills": task.extracted_skills or [],
        "search_keywords": task.search_keywords or [],
        "total_found": task.total_found,
        "total_saved": task.total_saved,
        "total_matched": task.total_matched,
        "failure_code": task.failure_code,
        "error_message": task.error_message,
        "crawl_diagnostics": task.crawl_diagnostics,
        "created_at": task.created_at,
        "started_at": task.started_at,
        "finished_at": task.finished_at,
    }
