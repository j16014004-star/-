"""Phase-one HR assistant orchestration with explicit user confirmation."""
from __future__ import annotations

import asyncio
import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.hr_application_agent import HrApplicationAgent
from app.ai.hr_reply_agent import HrReplyAgent
from app.ai.hr_interview_agent import HrInterviewAgent
from app.automations.job_58_apply import (
    PlatformJobClosed,
    PlatformJobMismatch,
    PlatformLoginExpired,
    PlatformNetworkDenied,
    apply_job_58,
    is_direct_58_job_url,
    read_messages_58,
    send_message_58,
)
from app.core.config import settings
from app.crud.ai_task import claim_provider_call, create_ai_task, get_ai_task
from app.crud.hr import (
    add_log,
    count_workspace_overview,
    create_action,
    create_interview,
    create_message,
    create_workspace,
    get_action,
    get_message,
    get_existing_application,
    get_existing_workspace,
    get_interview,
    get_latest_interview,
    get_owned_action,
    get_owned_workspace,
    get_owned_interview,
    get_workspace,
    list_logs,
    list_interviews,
    list_messages,
    list_workspace_actions,
    list_workspaces,
)
from app.crud.job import create_application, get_job_by_id
from app.crud.job_recommendation import get_latest_login_session
from app.crud.resume import get_resume_by_id
from app.crud.resume_optimization import get_owned_saved_optimization_version
from app.models.ai import AITask
from app.models.hr import HrInterview, HrMessage, HrPendingAction, HrWorkspace
from app.models.job import Job, JobPlatformLoginSession
from app.models.user import User
from app.schemas.hr import (
    HrActionConfirmRequest,
    HrMessageSendRequest,
    HrInterviewCreateRequest,
    HrInterviewDetectRequest,
    HrWorkspaceControlRequest,
    HrWorkspaceCreateRequest,
    HrWorkspaceModeRequest,
)
from app.services.recommendation_start_service import is_login_state_ready
from app.services.operational_alert_service import emit_operational_alert
from app.services.resume_delivery_service import build_resume_delivery_pdf
from app.workers.process_launcher import (
    WorkerLaunchError,
    launch_ai_task_worker,
    launch_hr_action_worker,
)


class HrServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(slots=True)
class ResumeSelection:
    text: str
    title: str
    resume_id: int
    resume_source: str
    resume_optimization_id: int | None
    original_file_path: str | None = None
    original_file_type: str | None = None


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def resolve_timezone(timezone_name: str):
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        if timezone_name == "Asia/Shanghai":
            return timezone(timedelta(hours=8), name="Asia/Shanghai")
        return timezone.utc


async def get_resume_selection(
    db: AsyncSession, *, user_id: int, resume_id: int,
    resume_source: str, resume_optimization_id: int | None,
) -> ResumeSelection:
    resume = await get_resume_by_id(db, resume_id, user_id)
    if not resume or resume.status != "completed" or not (resume.extracted_text or "").strip():
        raise HrServiceError("简历不存在、无权访问或尚未处理完成", 404)
    if resume_source == "original":
        if resume_optimization_id is not None:
            raise HrServiceError("原始简历不能提交优化版本ID", 422)
        return ResumeSelection(
            text=resume.extracted_text.strip(),
            title=resume.title or "原始简历",
            resume_id=resume.id,
            resume_source="original",
            resume_optimization_id=None,
            original_file_path=resume.file_path,
            original_file_type=resume.file_type,
        )
    if resume_source != "optimized" or resume_optimization_id is None:
        raise HrServiceError("简历来源参数无效", 422)
    version = await get_owned_saved_optimization_version(
        db, optimization_id=resume_optimization_id, user_id=user_id
    )
    if not version or version.resume_id != resume_id:
        raise HrServiceError("优化简历不存在、未保存或不属于当前原始简历", 404)
    return ResumeSelection(
        text=version.optimized_content.strip(),
        title=version.title or "优化简历",
        resume_id=resume.id,
        resume_source="optimized",
        resume_optimization_id=version.id,
    )


async def build_preflight(db: AsyncSession, *, user_id: int, job_id: int, source: str) -> dict:
    job = await get_job_by_id(db, job_id)
    session = await get_latest_login_session(db, user_id, source)
    existing_application = await get_existing_application(db, user_id=user_id, job_id=job_id)
    existing_workspace = (await db.execute(
        select(HrWorkspace)
        .where(
            HrWorkspace.user_id == user_id,
            HrWorkspace.job_id == job_id,
            HrWorkspace.status.in_((
                "draft", "applying", "applied", "communicating",
                "interview_pending", "interview_scheduled", "paused",
            )),
        )
        .order_by(HrWorkspace.updated_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    checks = {
        "job_exists": bool(job and job.is_active and job.source == source),
        "direct_job_url": bool(job and is_direct_58_job_url(job.source_url)),
        "login_ready": bool(session and is_login_state_ready(session)),
        "manual_login_verified": bool(session and session.manual_login_verified),
    }
    reasons = {
        "job_exists": "岗位不存在、已失效或来源不一致",
        "direct_job_url": "岗位缺少可核验的58同城详情链接",
        "login_ready": "58同城登录状态不可用，请重新登录",
        "manual_login_verified": "必须由用户本人在受控浏览器完成平台登录",
    }
    errors = [reasons[key] for key, passed in checks.items() if not passed]
    if session is None:
        platform_status = "not_logged_in"
    elif session.status == "logged_in" and not checks["login_ready"]:
        platform_status = "expired"
    elif session.status in ("logged_in", "expired", "failed"):
        platform_status = session.status
    else:
        platform_status = "unknown"
    return {
        "source": source,
        "source_name": "58同城" if source == "58" else source,
        "platform_login_status": platform_status,
        "manual_login_verified": checks["manual_login_verified"],
        "can_start": not errors,
        "reason": "；".join(errors) if errors else None,
        "checks": checks,
        "errors": errors,
        "already_applied": bool(existing_application),
        "next_action": (
            "resume_communication"
            if existing_application and existing_workspace
            else "start_application"
        ),
        "workspace_id": existing_workspace.id if existing_workspace else None,
        "login_session_id": session.id if session else None,
        "checked_at": utc_now_naive(),
    }


async def start_workspace(
    db: AsyncSession, *, user_id: int, request: HrWorkspaceCreateRequest
) -> tuple[HrWorkspace, bool]:
    if not request.manual_login_confirmed:
        raise HrServiceError("请先确认招聘平台账号由本人登录", 422)
    await db.execute(select(User.id).where(User.id == user_id).with_for_update())
    preflight = await build_preflight(db, user_id=user_id, job_id=request.job_id, source=request.source)
    if not preflight["can_start"]:
        raise HrServiceError("；".join(preflight["errors"]), 409)
    selection = await get_resume_selection(
        db, user_id=user_id, resume_id=request.resume_id,
        resume_source=request.resume_source,
        resume_optimization_id=request.resume_optimization_id,
    )
    existing = await get_existing_workspace(
        db, user_id=user_id, job_id=request.job_id, resume_id=request.resume_id,
        resume_source=request.resume_source,
        resume_optimization_id=request.resume_optimization_id,
    )
    if existing:
        existing.login_session_id = preflight["login_session_id"]
        existing.manual_login_verified = True
        existing.automation_mode = request.automation_mode
        existing.permissions = request.permissions.model_dump()
        if preflight["already_applied"]:
            existing.status = "communicating"
            existing.progress = 100
            existing.current_step = "平台已有投递记录，已进入HR沟通"
            existing.error_message = None
        auto_action = None
        if (
            request.automation_mode == "full_auto"
            and request.permissions.auto_apply
            and not preflight["already_applied"]
        ):
            auto_action = next(
                (
                    item for item in await list_workspace_actions(db, existing.id, user_id)
                    if item.action_type == "submit_application"
                    and item.status in ("waiting_confirmation", "failed")
                ),
                None,
            )
            if auto_action:
                auto_action.status = "pending"
                auto_action.error_message = None
                auto_action.requires_confirmation = False
                auto_action.approved_at = utc_now_naive()
                existing.status, existing.progress = "applying", 60
                existing.current_step = "正在执行已授权的AI投递"
                existing.pending_confirmation_count = max(
                    0, existing.pending_confirmation_count - 1
                )
        await db.commit()
        if auto_action:
            try:
                launch_hr_action_worker(auto_action.id)
            except WorkerLaunchError:
                await _mark_action_failed(auto_action.id, "无法启动平台投递任务")
        return existing, False
    if preflight["already_applied"]:
        workspace = await create_workspace(db, HrWorkspace(
            user_id=user_id, job_id=request.job_id, source=request.source,
            resume_id=request.resume_id, resume_source=request.resume_source,
            resume_optimization_id=request.resume_optimization_id,
            login_session_id=preflight["login_session_id"],
            automation_mode=request.automation_mode,
            permissions=request.permissions.model_dump(), manual_login_verified=True,
            status="communicating", progress=100,
            current_step="平台已有投递记录，已进入HR沟通",
        ))
        await add_log(
            db, workspace_id=workspace.id, user_id=user_id,
            action="application_existing",
            description="检测到该岗位已有投递记录，工作区直接进入HR沟通",
            status="success",
        )
        await db.commit()
        return workspace, True
    workspace = await create_workspace(db, HrWorkspace(
        user_id=user_id, job_id=request.job_id, source=request.source,
        resume_id=request.resume_id, resume_source=request.resume_source,
        resume_optimization_id=request.resume_optimization_id,
        login_session_id=preflight["login_session_id"],
        automation_mode=request.automation_mode,
        permissions=request.permissions.model_dump(), manual_login_verified=True,
        status="draft", progress=10, current_step="正在生成AI投递说明",
    ))
    input_hash = hashlib.sha256(
        f"{user_id}:{request.job_id}:{request.resume_id}:{request.resume_source}:"
        f"{request.resume_optimization_id}:{hashlib.sha256(selection.text.encode()).hexdigest()}".encode()
    ).hexdigest()
    task = AITask(
        id=str(uuid.uuid4()), user_id=user_id, task_type="hr_application_draft",
        resource_type="hr_workspace", resource_id=workspace.id, status="pending", progress=0,
        model_name=settings.HR_ASSISTANT_MODEL,
        prompt_version=settings.HR_APPLICATION_PROMPT_VERSION,
        input_hash=input_hash, request_payload={"workspace_id": workspace.id},
    )
    await create_ai_task(db, task)
    workspace.ai_task_id = task.id
    await add_log(db, workspace_id=workspace.id, user_id=user_id,
                  action="draft_requested", description="已提交AI投递说明生成任务", status="pending")
    await db.commit()
    try:
        launch_ai_task_worker(task.id)
    except WorkerLaunchError as exc:
        task.status, task.progress, task.error_message = "failed", 100, "无法启动AI生成任务"
        workspace.status, workspace.error_message = "failed", task.error_message
        await db.commit()
        raise HrServiceError(task.error_message, 503) from exc
    return workspace, True


async def execute_hr_application_draft_task(task_id: str) -> None:
    from app.core.database import async_session
    async with async_session() as db:
        task = await get_ai_task(db, task_id)
        workspace = await get_workspace(db, task.resource_id) if task else None
        if not task or task.status != "pending" or not workspace:
            return
        if not settings.TENCENT_MAAS_API_KEY.strip():
            await _mark_draft_failed(task_id, "未配置腾讯云 MaaS API Key")
            return
        job = await get_job_by_id(db, workspace.job_id)
        try:
            selection = await get_resume_selection(
                db, user_id=workspace.user_id, resume_id=workspace.resume_id,
                resume_source=workspace.resume_source,
                resume_optimization_id=workspace.resume_optimization_id,
            )
        except HrServiceError as exc:
            await db.rollback(); await _mark_draft_failed(task_id, exc.message); return
        if not job:
            await _mark_draft_failed(task_id, "岗位不存在"); return
        await claim_provider_call(db, task, utc_now_naive())
        task.status, task.progress, task.started_at = "generating", 30, utc_now_naive()
        await db.commit()
        job_data = {
            "title": job.title, "company": job.company, "city": job.city,
            "salary_min": job.salary_min, "salary_max": job.salary_max,
            "skills": job.skills or [], "description": job.description or "",
        }
    try:
        state = await HrApplicationAgent().run(job=job_data, resume_text=selection.text)
        result = state["result"]
        async with async_session() as db:
            task = await get_ai_task(db, task_id)
            workspace = await get_workspace(db, task.resource_id) if task else None
            if not task or not workspace: return
            key = hashlib.sha256(f"submit:{workspace.id}:{task.input_hash}".encode()).hexdigest()
            auto_apply = (
                workspace.automation_mode == "full_auto"
                and bool((workspace.permissions or {}).get("auto_apply"))
            )
            action = await create_action(db, HrPendingAction(
                workspace_id=workspace.id, user_id=workspace.user_id,
                action_type="submit_application",
                status="pending" if auto_apply else "waiting_confirmation",
                content=result.content.strip(), reason=result.reason.strip(),
                payload={
                    "job_id": workspace.job_id,
                    "resume_id": workspace.resume_id,
                    "resume_source": workspace.resume_source,
                    "resume_optimization_id": workspace.resume_optimization_id,
                },
                requires_confirmation=not auto_apply, idempotency_key=key,
                approved_at=utc_now_naive() if auto_apply else None,
            ))
            usage = state.get("token_usage") or {}
            prompt = int(usage.get("prompt_tokens") or 0); completion = int(usage.get("completion_tokens") or 0)
            task.token_usage = {"prompt_tokens": prompt, "completion_tokens": completion,
                                "total_tokens": int(usage.get("total_tokens") or prompt + completion),
                                "usage_reported": bool(usage)}
            task.model_name = state.get("used_model_name") or settings.HR_ASSISTANT_MODEL
            task.status, task.progress, task.result_id = "success", 100, action.id
            task.finished_at, task.error_message = utc_now_naive(), None
            workspace.status, workspace.progress = ("applying", 60) if auto_apply else ("draft", 40)
            workspace.current_step = "正在执行已授权的AI投递" if auto_apply else "等待用户确认投递"
            workspace.pending_confirmation_count = 0 if auto_apply else 1
            workspace.last_message = result.content[:500]
            workspace.last_message_at = utc_now_naive()
            await add_log(db, workspace_id=workspace.id, user_id=workspace.user_id,
                          action="draft_ready",
                          description=("AI投递说明已生成，正在按用户一键投递授权执行"
                                       if auto_apply else "AI投递说明已生成，等待用户确认"),
                          status="pending" if auto_apply else "waiting_confirmation")
            await db.commit()
            if auto_apply:
                try:
                    launch_hr_action_worker(action.id)
                except WorkerLaunchError:
                    await _mark_action_failed(action.id, "无法启动平台投递任务")
    except Exception as exc:
        await _mark_draft_failed(task_id, str(exc)[:500] or "AI投递说明生成失败")
        raise


async def _mark_draft_failed(task_id: str, message: str) -> None:
    from app.core.database import async_session
    async with async_session() as db:
        task = await get_ai_task(db, task_id)
        workspace = await get_workspace(db, task.resource_id) if task else None
        if not task or task.status == "success": return
        task.status, task.progress, task.error_message = "failed", 100, message[:500]
        task.finished_at = utc_now_naive()
        if workspace:
            workspace.status, workspace.error_message, workspace.current_step = "failed", message[:500], "AI生成失败"
            await add_log(db, workspace_id=workspace.id, user_id=workspace.user_id,
                          action="draft_failed", description=message, status="failed")
        await db.commit()


async def ensure_workspace_login(
    db: AsyncSession, workspace: HrWorkspace
) -> JobPlatformLoginSession:
    session = (await db.execute(select(JobPlatformLoginSession).where(
        JobPlatformLoginSession.id == workspace.login_session_id,
        JobPlatformLoginSession.user_id == workspace.user_id,
    ))).scalar_one_or_none()
    if not session or not session.manual_login_verified or not is_login_state_ready(session):
        raise HrServiceError("58同城登录状态不可用，请由本人重新登录", 409)
    return session


async def confirm_action(
    db: AsyncSession, *, user_id: int, workspace_id: int, action_id: int,
    request: HrActionConfirmRequest,
) -> HrWorkspace:
    workspace = await get_owned_workspace(db, workspace_id, user_id)
    action = await get_owned_action(db, action_id, workspace_id, user_id)
    if not workspace or not action: raise HrServiceError("工作区或待确认操作不存在", 404)
    if action.status != "waiting_confirmation":
        raise HrServiceError("该操作已处理，请勿重复确认", 409)
    action.confirmation_note = request.note
    if not request.approved:
        action.status = "rejected"
        workspace.pending_confirmation_count = max(0, workspace.pending_confirmation_count - 1)
        workspace.current_step = "用户已拒绝本次操作"
        if action.action_type == "send_message" and action.payload:
            message = await get_message(db, int(action.payload.get("message_id") or 0))
            if message:
                message.status = "failed"
        if action.action_type == "schedule_interview" and action.payload:
            interview = await get_interview(db, int(action.payload.get("interview_id") or 0))
            message = await get_message(db, int(action.payload.get("message_id") or 0))
            if interview:
                interview.status = "rejected"
            if message:
                message.status = "failed"
        await add_log(db, workspace_id=workspace.id, user_id=user_id,
                      action="action_rejected", description="用户拒绝了本次待执行操作", status="rejected")
        await db.commit(); return workspace
    if action.action_type == "submit_application":
        preflight = await build_preflight(db, user_id=user_id, job_id=workspace.job_id, source=workspace.source)
        if not preflight["can_start"]: raise HrServiceError("；".join(preflight["errors"]), 409)
    elif action.action_type in ("send_message", "schedule_interview"):
        await ensure_workspace_login(db, workspace)
    else:
        raise HrServiceError("当前不支持该操作类型", 422)
    action.status, action.approved_at = "pending", utc_now_naive()
    if action.action_type == "send_message":
        workspace.status, workspace.current_step = "communicating", "正在发送已确认的消息"
    elif action.action_type == "schedule_interview":
        workspace.status, workspace.current_step = "interview_pending", "正在发送面试确认"
    else:
        workspace.status, workspace.progress, workspace.current_step = "applying", 60, "正在执行已确认的投递"
    workspace.pending_confirmation_count = max(0, workspace.pending_confirmation_count - 1)
    await add_log(db, workspace_id=workspace.id, user_id=user_id,
                  action="action_approved", description="用户已确认操作，等待平台执行", status="pending")
    await db.commit()
    try: launch_hr_action_worker(action.id)
    except WorkerLaunchError as exc:
        action.status, action.error_message = "failed", "无法启动平台操作任务"
        workspace.status, workspace.error_message = "failed", action.error_message
        await db.commit(); raise HrServiceError(action.error_message, 503) from exc
    return workspace


async def execute_hr_apply_action(action_id: int) -> None:
    from app.core.database import async_session
    async with async_session() as db:
        action = await get_action(db, action_id)
        if action and action.action_type == "send_message":
            await db.rollback()
            return await execute_hr_send_message_action(action_id)
        if action and action.action_type == "schedule_interview":
            await db.rollback()
            return await execute_hr_interview_action(action_id)
        workspace = await get_workspace(db, action.workspace_id) if action else None
        if not action or not workspace or action.status != "pending": return
        job = await get_job_by_id(db, workspace.job_id)
        session = (await db.execute(select(JobPlatformLoginSession).where(
            JobPlatformLoginSession.id == workspace.login_session_id))).scalar_one_or_none()
        if not job or not session or not is_login_state_ready(session) or not session.manual_login_verified:
            action.status, action.error_message = "failed", "登录状态或岗位信息已失效，请重新登录后重试"
            workspace.status, workspace.error_message = "paused", action.error_message
            await db.commit(); return
        try:
            selection = await get_resume_selection(
                db,
                user_id=workspace.user_id,
                resume_id=workspace.resume_id,
                resume_source=workspace.resume_source,
                resume_optimization_id=workspace.resume_optimization_id,
            )
        except HrServiceError as exc:
            action.status, action.error_message = "failed", exc.message
            workspace.status, workspace.error_message = "paused", exc.message
            await db.commit()
            return
        action.status = "executing"; await db.commit()
        context = {"storage_state": session.storage_state_ref, "source_url": job.source_url,
                   "expected_title": job.title, "expected_source_id": job.source_id,
                   "greeting": action.content,
                   "session_id": session.id, "user_id": workspace.user_id,
                   "workspace_id": workspace.id, "selection": selection}
    try:
        selection = context["selection"]
        artifact = await build_resume_delivery_pdf(
            user_id=context["user_id"],
            workspace_id=context["workspace_id"],
            resume_id=selection.resume_id,
            resume_source=selection.resume_source,
            resume_optimization_id=selection.resume_optimization_id,
            title=selection.title,
            text=selection.text,
            original_file_path=selection.original_file_path,
            original_file_type=selection.original_file_type,
        )
        result = await apply_job_58(**{k: context[k] for k in (
            "storage_state", "source_url", "expected_title", "expected_source_id", "greeting"
        )}, resume_file_path=artifact.path, resume_file_name=artifact.file_name,
            resume_file_sha256=artifact.sha256)
        async with async_session() as db:
            action = await get_action(db, action_id); workspace = await get_workspace(db, action.workspace_id) if action else None
            if not action or not workspace: return
            job = await get_job_by_id(db, workspace.job_id)
            final_url = (result.get("final_url") or "").strip()
            if job and is_direct_58_job_url(final_url):
                job.source_url = final_url[:500]
            await db.execute(
                select(User.id)
                .where(User.id == workspace.user_id)
                .with_for_update()
            )
            existing = await get_existing_application(db, user_id=workspace.user_id, job_id=workspace.job_id)
            delivery_evidence = {
                "resume_id": artifact.resume_id,
                "resume_source": artifact.resume_source,
                "resume_optimization_id": artifact.resume_optimization_id,
                "file_name": artifact.file_name,
                "file_sha256": artifact.sha256,
                "platform_job_id": job.source_id if job else None,
                "delivery_strategy": result.get("resume_delivery_strategy"),
                "resume_verified": bool(result.get("resume_verified")),
                "platform_evidence": result.get("evidence"),
                "final_url": result.get("final_url"),
            }
            if not existing:
                await create_application(db, workspace.user_id, workspace.job_id, workspace.resume_id,
                    action.content, workspace.resume_source, workspace.resume_optimization_id,
                    apply_type="agent", delivery_evidence=delivery_evidence)
            elif not existing.delivery_evidence:
                existing.delivery_evidence = delivery_evidence
            now = utc_now_naive(); action.status, action.executed_at, action.error_message = "success", now, None
            application_status = result.get("application_status") or "submitted"
            action.payload = {
                **(action.payload or {}),
                "platform_evidence": result.get("evidence"),
                "final_url": result.get("final_url"),
                "application_status": application_status,
                "resume_delivery": delivery_evidence,
            }
            workspace.status, workspace.progress = "communicating", 100
            workspace.current_step = (
                "平台显示已申请，已进入HR沟通"
                if application_status == "already_applied"
                else "平台已确认投递成功，已进入HR沟通"
            )
            workspace.applied_at, workspace.error_message = now, None
            await add_log(db, workspace_id=workspace.id, user_id=workspace.user_id,
                          action=("application_existing" if application_status == "already_applied"
                                  else "application_success"),
                          description=f"58同城返回明确申请标识：{result.get('evidence')}，进入HR沟通",
                          status="success")
            await db.commit()
            if workspace.automation_mode == "full_auto":
                try:
                    await sync_workspace_messages(
                        db,
                        user_id=workspace.user_id,
                        workspace_id=workspace.id,
                    )
                except HrServiceError:
                    # The durable scheduler will retry; application success must
                    # not be rolled back by a temporary WebIM loading failure.
                    pass
    except PlatformLoginExpired as exc:
        await _mark_action_failed(action_id, str(exc), login_expired=True, session_id=context["session_id"])
    except PlatformJobClosed as exc:
        await _mark_action_failed(action_id, str(exc))
        async with async_session() as db:
            action = await get_action(db, action_id)
            workspace = await get_workspace(db, action.workspace_id) if action else None
            job = await get_job_by_id(db, workspace.job_id) if workspace else None
            if job:
                job.is_active = False
                await db.commit()
    except PlatformJobMismatch as exc:
        await _mark_action_failed(action_id, str(exc))
        async with async_session() as db:
            action = await get_action(db, action_id)
            workspace = await get_workspace(db, action.workspace_id) if action else None
            job = await get_job_by_id(db, workspace.job_id) if workspace else None
            if job:
                job.is_active = False
                await db.commit()
    except Exception as exc:
        await _mark_action_failed(action_id, str(exc)[:500] or "投递执行失败")


async def _mark_action_failed(
    action_id: int, error_message: str, *, login_expired: bool = False,
    session_id: str | None = None,
) -> None:
    from app.core.database import async_session
    async with async_session() as db:
        action = await get_action(db, action_id); workspace = await get_workspace(db, action.workspace_id) if action else None
        if not action or not workspace: return
        safe_error = error_message[:500]
        action.status, action.error_message = "failed", safe_error
        if action.action_type == "send_message" and action.payload:
            pending_message = await get_message(db, int(action.payload.get("message_id") or 0))
            if pending_message:
                pending_message.status = "failed"
        if action.action_type == "schedule_interview" and action.payload:
            interview = await get_interview(db, int(action.payload.get("interview_id") or 0))
            pending_message = await get_message(db, int(action.payload.get("message_id") or 0))
            if interview:
                interview.status = "failed"
            if pending_message:
                pending_message.status = "failed"
        workspace.status, workspace.error_message = "paused", safe_error
        workspace.current_step = "请重新登录后重试" if login_expired else "平台执行失败，请手动接管"
        if login_expired and session_id:
            session = (await db.execute(select(JobPlatformLoginSession).where(JobPlatformLoginSession.id == session_id))).scalar_one_or_none()
            if session: session.status, session.error_message = "expired", safe_error
        await add_log(db, workspace_id=workspace.id, user_id=workspace.user_id,
                      action=("interview_failed" if action.action_type == "schedule_interview"
                              else "message_failed" if action.action_type == "send_message"
                              else "application_failed"),
                      description=safe_error, status="failed")
        await db.commit()
        emit_operational_alert(
            category="hr_action_failed",
            message=safe_error,
            context={
                "action_id": action.id,
                "action_type": action.action_type,
                "workspace_id": workspace.id,
                "user_id": workspace.user_id,
                "login_expired": login_expired,
            },
        )


async def update_workspace_mode(
    db: AsyncSession, *, user_id: int, workspace_id: int, request: HrWorkspaceModeRequest
) -> dict:
    workspace = await get_owned_workspace(db, workspace_id, user_id)
    if not workspace:
        raise HrServiceError("HR工作区不存在", 404)
    if workspace.status in ("completed", "cancelled"):
        raise HrServiceError("已结束的工作区不能修改模式", 409)
    if request.automation_mode in ("full_auto", "assisted"):
        await ensure_workspace_login(db, workspace)
    workspace.automation_mode = request.automation_mode
    workspace.permissions = request.permissions.model_dump()
    mode_text = {
        "manual": "已切换为人工模式",
        "assisted": "已切换为辅助模式",
        "full_auto": "已切换为全自动模式",
    }
    workspace.current_step = mode_text[request.automation_mode]
    await add_log(db, workspace_id=workspace.id, user_id=user_id, action="mode_changed",
                  description=f"工作区模式已切换为 {request.automation_mode}", status="success")
    await db.commit()
    return await workspace_detail(db, user_id=user_id, workspace_id=workspace_id)


async def control_workspace(
    db: AsyncSession, *, user_id: int, workspace_id: int, request: HrWorkspaceControlRequest
) -> dict:
    workspace = await get_owned_workspace(db, workspace_id, user_id)
    if not workspace:
        raise HrServiceError("HR工作区不存在", 404)
    if workspace.status == "cancelled":
        raise HrServiceError("工作区已终止，不能继续操作", 409)
    descriptions = {
        "pause": "用户已暂停自动化操作",
        "resume": "用户已恢复工作区",
        "take_over": "用户已人工接管，自动发送权限全部关闭",
        "terminate": "用户已终止工作区",
    }
    if request.action == "resume":
        await ensure_workspace_login(db, workspace)
        application = await get_existing_application(db, user_id=user_id, job_id=workspace.job_id)
        workspace.status = "communicating" if application else "draft"
        workspace.current_step = "工作区已恢复"
        workspace.error_message = None
    elif request.action == "pause":
        workspace.status, workspace.current_step = "paused", "用户已暂停"
    elif request.action == "take_over":
        workspace.automation_mode = "manual"
        workspace.permissions = {
            "auto_apply": False, "auto_greeting": False,
            "auto_reply": False, "auto_schedule_interview": False,
        }
        workspace.status, workspace.current_step = "paused", "用户已人工接管"
    else:
        workspace.status, workspace.current_step = "cancelled", "工作区已终止"
    await add_log(db, workspace_id=workspace.id, user_id=user_id, action=request.action,
                  description=descriptions[request.action], status="success")
    await db.commit()
    return await workspace_detail(db, user_id=user_id, workspace_id=workspace_id)


def serialize_message(message: HrMessage) -> dict:
    return {
        "id": message.id, "workspace_id": message.workspace_id,
        "action_id": message.action_id,
        "sender_type": message.sender_type, "content": message.content,
        "status": message.status, "is_ai_generated": message.is_ai_generated,
        "requires_confirmation": message.requires_confirmation,
        "sent_at": message.sent_at, "created_at": message.created_at,
    }


async def get_workspace_messages(db: AsyncSession, *, user_id: int, workspace_id: int) -> dict:
    workspace = await get_owned_workspace(db, workspace_id, user_id)
    if not workspace:
        raise HrServiceError("HR工作区不存在", 404)
    items = await list_messages(db, workspace_id, user_id)
    changed = False
    for item in items:
        if item.sender_type == "hr" and item.status == "sent":
            item.status = "read"
            changed = True
    if changed or workspace.unread_count:
        workspace.unread_count = 0
        await db.commit()
    return {"items": [serialize_message(item) for item in items], "total": len(items)}


async def sync_workspace_messages(db: AsyncSession, *, user_id: int, workspace_id: int) -> dict:
    workspace = await get_owned_workspace(db, workspace_id, user_id)
    if not workspace:
        raise HrServiceError("HR工作区不存在", 404)
    if workspace.status in ("completed", "cancelled"):
        raise HrServiceError("已结束的工作区不能同步消息", 409)
    try:
        session = await ensure_workspace_login(db, workspace)
    except HrServiceError as exc:
        session = (await db.execute(select(JobPlatformLoginSession).where(
            JobPlatformLoginSession.id == workspace.login_session_id,
            JobPlatformLoginSession.user_id == workspace.user_id,
        ))).scalar_one_or_none()
        if session:
            session.status, session.error_message = "expired", exc.message[:500]
        workspace.status = "paused"
        workspace.current_step = "58同城登录失效，请重新登录"
        workspace.error_message = exc.message[:500]
        workspace.sync_status = "login_expired"
        workspace.sync_error = exc.message[:500]
        workspace.last_synced_at = utc_now_naive()
        await add_log(
            db,
            workspace_id=workspace.id,
            user_id=user_id,
            action="platform_login_expired",
            description="58同城登录状态失效，后台消息监控已停止，请重新登录",
            status="failed",
        )
        await db.commit()
        raise
    job = await get_job_by_id(db, workspace.job_id)
    if not job:
        raise HrServiceError("岗位不存在", 404)
    was_network_paused = (
        workspace.status == "paused" and workspace.sync_status == "network_denied"
    )
    claim_time = utc_now_naive()
    stale_before = claim_time - timedelta(minutes=2)
    claim = await db.execute(
        update(HrWorkspace)
        .where(
            HrWorkspace.id == workspace.id,
            HrWorkspace.user_id == user_id,
            or_(
                HrWorkspace.sync_status != "syncing",
                HrWorkspace.last_synced_at.is_(None),
                HrWorkspace.last_synced_at < stale_before,
            ),
        )
        .values(
            sync_status="syncing",
            sync_error=None,
            last_synced_at=claim_time,
        )
    )
    if claim.rowcount != 1:
        await db.rollback()
        await db.refresh(workspace)
        return {
            "new_messages": 0,
            "unread_count": workspace.unread_count,
            "platform_login_status": session.status,
            "sync_status": "syncing",
            "sync_error": None,
            "last_synced_at": workspace.last_synced_at,
            "platform_snapshot": workspace.platform_snapshot,
            "automation_action": None,
            "sync_skipped": True,
        }
    await db.commit()
    await db.refresh(workspace)
    try:
        result = await read_messages_58(
            storage_state=session.storage_state_ref, source_url=job.source_url,
            thread_url=workspace.platform_thread_url, expected_title=job.title,
            expected_source_id=job.source_id,
        )
    except PlatformLoginExpired as exc:
        session.status, session.error_message = "expired", str(exc)[:500]
        workspace.status = "paused"
        workspace.current_step = "58同城登录失效，请重新登录"
        workspace.error_message = str(exc)[:500]
        workspace.sync_status = "login_expired"
        workspace.sync_error = str(exc)[:500]
        workspace.last_synced_at = utc_now_naive()
        await add_log(
            db,
            workspace_id=workspace.id,
            user_id=user_id,
            action="platform_login_expired",
            description="58同城登录状态失效，后台消息监控已停止，请重新登录",
            status="failed",
        )
        await db.commit()
        raise HrServiceError(str(exc), 409) from exc
    except PlatformNetworkDenied as exc:
        message = str(exc)[:500]
        workspace.status = "paused"
        workspace.current_step = "运行环境无法访问58同城，后台消息监控已暂停"
        workspace.error_message = message
        workspace.sync_status = "network_denied"
        workspace.sync_error = message
        workspace.last_synced_at = utc_now_naive()
        await add_log(
            db,
            workspace_id=workspace.id,
            user_id=user_id,
            action="platform_network_denied",
            description=message,
            status="failed",
        )
        await db.commit()
        raise HrServiceError(message, 503) from exc
    except Exception as exc:
        detail = str(exc).strip()
        message = (detail or f"{type(exc).__name__}: 未提供详细错误")[:500]
        workspace.sync_status = "failed"
        workspace.sync_error = message
        workspace.last_synced_at = utc_now_naive()
        await add_log(
            db,
            workspace_id=workspace.id,
            user_id=user_id,
            action="platform_sync_failed",
            description=message,
            status="failed",
        )
        await db.commit()
        raise HrServiceError(message, 502) from exc
    # Serialize concurrent scheduler/manual sync calls before deduplication and inserts.
    await db.execute(
        select(HrWorkspace.id)
        .where(HrWorkspace.id == workspace.id, HrWorkspace.user_id == user_id)
        .with_for_update()
    )
    existing = await list_messages(db, workspace.id, user_id)
    existing_refs = {item.platform_message_ref for item in existing if item.platform_message_ref}
    added = 0
    for item in result.get("messages") or []:
        if item.get("sender_type") != "hr":
            continue
        reference = platform_message_reference(item)
        if reference in existing_refs:
            continue
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        legacy = next(
            (
                message for message in existing
                if message.sender_type == "hr"
                and message.content == content
                and not str(message.platform_message_ref or "").startswith("58:")
            ),
            None,
        )
        if legacy:
            legacy.platform_message_ref = reference
            existing_refs.add(reference)
            continue
        await create_message(db, HrMessage(
            workspace_id=workspace.id, user_id=user_id, sender_type="hr",
            content=content, status="sent", is_ai_generated=False,
            requires_confirmation=False, platform_message_ref=reference,
            sent_at=utc_now_naive(),
        ))
        existing_refs.add(reference); added += 1
        workspace.last_message, workspace.last_message_at = content[:500], utc_now_naive()
    workspace.platform_thread_url = (
        result.get("thread_url") or workspace.platform_thread_url
    )
    workspace.platform_conversation_id = (
        result.get("conversation_id") or workspace.platform_conversation_id
    )
    conversation_label = str(result.get("conversation_label") or "").strip()
    if conversation_label:
        workspace.hr_name = conversation_label[:100]
    workspace.platform_snapshot = {
        "source": "58",
        "application_status": "communicating",
        "conversation_id": workspace.platform_conversation_id,
        "conversation_label": conversation_label or workspace.hr_name,
        "thread_available": bool(workspace.platform_thread_url),
        "thread_inline": bool(result.get("thread_inline")),
        "selector_used": result.get("selector_used"),
        "message_node_count": int(result.get("message_node_count") or 0),
        "received_message_count": len(result.get("messages") or []),
    }
    workspace.sync_status = "success"
    workspace.sync_error = None
    workspace.last_synced_at = utc_now_naive()
    workspace.error_message = None
    if was_network_paused:
        workspace.status = "communicating"
        workspace.current_step = "平台连接已恢复，等待HR消息"
    workspace.unread_count += added
    if added:
        workspace.status, workspace.current_step = "communicating", "收到HR新消息"
        await add_log(db, workspace_id=workspace.id, user_id=user_id, action="messages_synced",
                      description=f"从平台同步到 {added} 条HR新消息", status="success")
    await db.commit()
    automation = await process_workspace_automation(
        db, workspace=workspace
    )
    return {
        "new_messages": added,
        "unread_count": workspace.unread_count,
        "platform_login_status": session.status,
        "sync_status": workspace.sync_status,
        "sync_error": workspace.sync_error,
        "last_synced_at": workspace.last_synced_at,
        "platform_snapshot": workspace.platform_snapshot,
        **automation,
    }


def platform_message_reference(item: dict) -> str:
    """Prefer the platform message ID; otherwise hash sender, content and platform time."""
    platform_id = str(item.get("platform_message_id") or "").strip()
    if platform_id:
        return f"58:id:{platform_id}"[:200]
    sender = str(item.get("sender_type") or "").strip()
    content = " ".join(str(item.get("content") or "").split())
    message_time = str(item.get("message_time") or "").strip()
    digest = hashlib.sha256(
        f"{sender}\n{content}\n{message_time}".encode("utf-8")
    ).hexdigest()
    return f"58:fallback:{digest}"


def message_requires_confirmation(content: str) -> bool:
    normalized = "".join(content.lower().split())
    markers = (
        "身份证", "银行卡", "验证码", "密码", "付费", "转账", "押金", "保证金",
        "offer", "录用承诺", "入职承诺", "薪资承诺", "工资承诺",
        "接受offer", "确认offer", "薪资确认", "期望薪资", "最低薪资",
        "确认面试", "面试时间", "家庭住址", "详细地址",
    )
    salary_commitment = (
        any(marker in normalized for marker in ("薪资", "工资", "报酬"))
        and any(marker in normalized for marker in ("承诺", "接受", "确认", "同意"))
    )
    return salary_commitment or any(marker in normalized for marker in markers)


async def create_outgoing_message(
    db: AsyncSession, *, user_id: int, workspace_id: int, request: HrMessageSendRequest
) -> dict:
    workspace = await get_owned_workspace(db, workspace_id, user_id)
    if not workspace:
        raise HrServiceError("HR工作区不存在", 404)
    if workspace.status in ("paused", "completed", "cancelled", "failed"):
        raise HrServiceError("当前工作区状态不允许发送消息", 409)
    await ensure_workspace_login(db, workspace)
    content = request.content.strip()
    high_risk = message_requires_confirmation(content)
    message = await create_message(db, HrMessage(
        workspace_id=workspace.id, user_id=user_id, sender_type="user", content=content,
        status="pending_confirmation" if high_risk else "sending",
        is_ai_generated=request.send_mode == "ai_suggestion",
        requires_confirmation=high_risk,
    ))
    key = hashlib.sha256(f"message:{workspace.id}:{message.id}:{content}".encode()).hexdigest()
    action = await create_action(db, HrPendingAction(
        workspace_id=workspace.id, user_id=user_id, action_type="send_message",
        status="waiting_confirmation" if high_risk else "pending", content=content,
        reason="消息包含敏感承诺或隐私信息，需要再次确认" if high_risk else "用户已明确点击发送",
        payload={"message_id": message.id}, requires_confirmation=high_risk,
        idempotency_key=key,
        approved_at=None if high_risk else utc_now_naive(),
    ))
    message.action_id = action.id
    workspace.status = "communicating"
    workspace.current_step = "等待用户确认敏感消息" if high_risk else "正在发送消息"
    if high_risk:
        workspace.pending_confirmation_count += 1
    await add_log(db, workspace_id=workspace.id, user_id=user_id, action="message_queued",
                  description=workspace.current_step, status=action.status)
    await db.commit()
    if not high_risk:
        try:
            launch_hr_action_worker(action.id)
        except WorkerLaunchError as exc:
            action.status, message.status = "failed", "failed"
            action.error_message = "无法启动消息发送任务"
            workspace.status, workspace.error_message = "paused", action.error_message
            await db.commit()
            raise HrServiceError(action.error_message, 503) from exc
    return {"message": serialize_message(message), "action_id": action.id,
            "waiting_confirmation": high_risk}


async def generate_reply_suggestions(
    db: AsyncSession, *, user_id: int, workspace_id: int
) -> dict:
    workspace = await get_owned_workspace(db, workspace_id, user_id)
    if not workspace:
        raise HrServiceError("HR工作区不存在", 404)
    if workspace.status in ("completed", "cancelled"):
        raise HrServiceError("已结束的工作区不能生成回复", 409)
    if not settings.TENCENT_MAAS_API_KEY.strip():
        raise HrServiceError("未配置腾讯云 MaaS API Key", 503)
    selection = await get_resume_selection(
        db, user_id=user_id, resume_id=workspace.resume_id,
        resume_source=workspace.resume_source,
        resume_optimization_id=workspace.resume_optimization_id,
    )
    job = await get_job_by_id(db, workspace.job_id)
    messages = await list_messages(db, workspace.id, user_id)
    history = [{"sender_type": item.sender_type, "content": item.content} for item in messages]
    input_hash = hashlib.sha256(
        f"{workspace.id}:{history}:{selection.text}".encode()
    ).hexdigest()
    task = AITask(
        id=str(uuid.uuid4()), user_id=user_id, task_type="hr_reply_suggestion",
        resource_type="hr_workspace", resource_id=workspace.id,
        status="generating", progress=30, model_name=settings.HR_ASSISTANT_MODEL,
        prompt_version=settings.HR_REPLY_PROMPT_VERSION, input_hash=input_hash,
        request_payload={"workspace_id": workspace.id},
        provider_call_started_at=utc_now_naive(), started_at=utc_now_naive(),
    )
    await create_ai_task(db, task); await db.commit()
    try:
        state = await HrReplyAgent().run(
            job={"title": job.title, "company": job.company, "skills": job.skills or [],
                 "description": job.description or ""} if job else {},
            resume_text=selection.text, messages=history,
        )
        usage = state.get("token_usage") or {}
        prompt = int(usage.get("prompt_tokens") or 0); completion = int(usage.get("completion_tokens") or 0)
        task.status, task.progress, task.finished_at = "success", 100, utc_now_naive()
        task.model_name = state.get("used_model_name") or settings.HR_ASSISTANT_MODEL
        task.token_usage = {"prompt_tokens": prompt, "completion_tokens": completion,
                            "total_tokens": int(usage.get("total_tokens") or prompt + completion),
                            "usage_reported": bool(usage)}
        task.request_payload = {
            **(task.request_payload or {}),
            "retrieval_source": state.get("retrieval_source"),
            "retrieval_error": state.get("retrieval_error"),
            "retrieval_audit": state.get("retrieval_audit") or [],
        }
        await db.commit()
        return {
            "items": [item.model_dump() for item in state["result"].items],
            "ai_task_id": task.id,
            "retrieval_source": state.get("retrieval_source"),
            "retrieval_error": state.get("retrieval_error"),
            "retrieved_chunks": state.get("retrieval_audit") or [],
        }
    except Exception as exc:
        task.status, task.progress, task.finished_at = "failed", 100, utc_now_naive()
        task.error_message = (str(exc).strip() or "AI回复建议生成失败")[:500]
        await db.commit()
        raise HrServiceError(task.error_message, 502) from exc


async def execute_hr_send_message_action(action_id: int) -> None:
    from app.core.database import async_session
    async with async_session() as db:
        action = await get_action(db, action_id)
        workspace = await get_workspace(db, action.workspace_id) if action else None
        message_id = int((action.payload or {}).get("message_id") or 0) if action else 0
        message = await get_message(db, message_id)
        if not action or not workspace or not message or action.status != "pending":
            return
        job = await get_job_by_id(db, workspace.job_id)
        try:
            session = await ensure_workspace_login(db, workspace)
        except HrServiceError as exc:
            await db.rollback(); await _mark_action_failed(action_id, exc.message, login_expired=True,
                                                            session_id=workspace.login_session_id); return
        if not job:
            await db.rollback(); await _mark_action_failed(action_id, "岗位不存在"); return
        action.status, message.status = "executing", "sending"
        await db.commit()
        context = {"storage_state": session.storage_state_ref, "source_url": job.source_url,
                   "thread_url": workspace.platform_thread_url, "expected_title": job.title,
                   "expected_source_id": job.source_id,
                   "content": message.content, "session_id": session.id}
    try:
        result = await send_message_58(**{k: context[k] for k in (
            "storage_state", "source_url", "thread_url", "expected_title",
            "expected_source_id", "content"
        )})
        async with async_session() as db:
            action = await get_action(db, action_id)
            workspace = await get_workspace(db, action.workspace_id) if action else None
            message = await get_message(db, int((action.payload or {}).get("message_id") or 0)) if action else None
            if not action or not workspace or not message:
                return
            now = utc_now_naive()
            action.status, action.executed_at, action.error_message = "success", now, None
            action.payload = {**(action.payload or {}), "platform_evidence": result["evidence"]}
            message.status, message.sent_at = "sent", now
            message.platform_message_ref = hashlib.sha256(
                f"{workspace.id}:{message.id}:{message.content}".encode()
            ).hexdigest()
            workspace.platform_thread_url = (
                result.get("thread_url") or workspace.platform_thread_url
            )
            workspace.platform_conversation_id = (
                result.get("conversation_id") or workspace.platform_conversation_id
            )
            conversation_label = str(result.get("conversation_label") or "").strip()
            if conversation_label:
                workspace.hr_name = conversation_label[:100]
            workspace.platform_snapshot = {
                **(workspace.platform_snapshot or {}),
                "source": "58",
                "application_status": "communicating",
                "conversation_id": workspace.platform_conversation_id,
                "conversation_label": conversation_label or workspace.hr_name,
                "thread_available": bool(workspace.platform_thread_url),
            }
            workspace.sync_status = "success"
            workspace.sync_error = None
            workspace.status, workspace.current_step = "communicating", "消息已发送，等待HR回复"
            workspace.last_message, workspace.last_message_at = message.content[:500], now
            workspace.error_message = None
            await add_log(db, workspace_id=workspace.id, user_id=workspace.user_id,
                          action="message_sent", description="平台已核验消息出现在会话中", status="success")
            await db.commit()
    except PlatformLoginExpired as exc:
        await _mark_action_failed(action_id, str(exc), login_expired=True, session_id=context["session_id"])
    except Exception as exc:
        await _mark_action_failed(action_id, str(exc)[:500] or "消息发送失败")


def to_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise HrServiceError("面试时间必须包含时区", 422)
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def parse_ai_interview_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HrServiceError("AI提取的面试时间格式无效，需要用户手动确认", 422) from exc
    return to_utc_naive(parsed)


def serialize_interview(interview: HrInterview) -> dict:
    scheduled_at = (
        interview.scheduled_at.replace(tzinfo=timezone.utc)
        if interview.scheduled_at and interview.scheduled_at.tzinfo is None
        else interview.scheduled_at
    )
    end_at = (
        interview.end_at.replace(tzinfo=timezone.utc)
        if interview.end_at and interview.end_at.tzinfo is None
        else interview.end_at
    )
    return {
        "id": interview.id, "workspace_id": interview.workspace_id,
        "source_message_id": interview.source_message_id, "action_id": interview.action_id,
        "status": interview.status, "scheduled_at": scheduled_at,
        "end_at": end_at, "timezone": interview.timezone,
        "interview_type": interview.interview_type, "location": interview.location,
        "meeting_url": interview.meeting_url, "contact_name": interview.contact_name,
        "evidence": interview.evidence, "missing_fields": interview.missing_fields or [],
        "suggested_reply": interview.suggested_reply,
        "requires_confirmation": interview.requires_confirmation,
        "confirmed_at": interview.confirmed_at, "created_at": interview.created_at,
    }


def required_interview_fields_missing(
    *,
    scheduled_at: datetime | None,
    interview_type: str | None,
    location: str | None,
    meeting_url: str | None,
) -> list[str]:
    """Return only fields required to safely propose this interview arrangement."""
    missing: list[str] = []
    if scheduled_at is None:
        missing.append("scheduled_at")
    normalized_type = "".join((interview_type or "").lower().split())
    if not normalized_type:
        missing.append("interview_type")
        return missing
    if any(marker in normalized_type for marker in ("视频", "线上", "在线", "远程", "online")):
        if not meeting_url:
            missing.append("meeting_url")
    elif any(marker in normalized_type for marker in ("现场", "线下", "到店", "面谈", "onsite")):
        if not location:
            missing.append("location")
    elif any(marker in normalized_type for marker in ("电话", "语音", "phone")):
        pass
    elif not location and not meeting_url:
        missing.append("location_or_meeting_url")
    return missing


def build_interview_confirmation_reply(
    *,
    scheduled_at: datetime,
    timezone_name: str,
    interview_type: str,
    location: str | None,
    meeting_url: str | None,
) -> str:
    """Build a fact-only draft; sending always remains behind user confirmation."""
    target_timezone = resolve_timezone(timezone_name)
    local_time = scheduled_at.replace(tzinfo=timezone.utc).astimezone(target_timezone)
    details = [f"{local_time:%Y年%m月%d日 %H:%M}", interview_type]
    if location:
        details.append(f"地点：{location}")
    if meeting_url:
        details.append(f"链接：{meeting_url}")
    return f"感谢您的面试邀请，我可以参加{'，'.join(details)}的面试，请您确认。"


async def attach_interview_confirmation(
    db: AsyncSession, *, workspace: HrWorkspace, interview: HrInterview, reply_content: str,
    ai_generated: bool,
) -> HrPendingAction:
    message = await create_message(db, HrMessage(
        workspace_id=workspace.id, user_id=workspace.user_id,
        sender_type="ai" if ai_generated else "user",
        content=reply_content.strip(), status="pending_confirmation",
        is_ai_generated=ai_generated, requires_confirmation=True,
    ))
    key = hashlib.sha256(
        f"interview:{workspace.id}:{interview.id}:{reply_content}".encode()
    ).hexdigest()
    action = await create_action(db, HrPendingAction(
        workspace_id=workspace.id, user_id=workspace.user_id,
        action_type="schedule_interview", status="waiting_confirmation",
        content=reply_content.strip(), reason="面试时间确认属于重要操作，必须由用户确认",
        payload={"interview_id": interview.id, "message_id": message.id},
        requires_confirmation=True, idempotency_key=key,
    ))
    message.action_id = action.id
    interview.action_id = action.id
    workspace.status, workspace.current_step = "interview_pending", "等待用户确认面试安排"
    workspace.pending_confirmation_count += 1
    await add_log(db, workspace_id=workspace.id, user_id=workspace.user_id,
                  action="interview_proposed", description="已识别面试安排，等待用户确认",
                  status="waiting_confirmation")
    return action


async def detect_interview_invitation(
    db: AsyncSession, *, user_id: int, workspace_id: int, request: HrInterviewDetectRequest
) -> dict:
    workspace = await get_owned_workspace(db, workspace_id, user_id)
    if not workspace:
        raise HrServiceError("HR工作区不存在", 404)
    messages = await list_messages(db, workspace.id, user_id)
    if request.message_id:
        source = next((item for item in messages if item.id == request.message_id), None)
    else:
        source = next((item for item in reversed(messages) if item.sender_type == "hr"), None)
    if not source or source.sender_type != "hr":
        raise HrServiceError("没有可用于识别的HR消息", 404)
    existing = next((item for item in await list_interviews(db, workspace.id, user_id)
                     if item.source_message_id == source.id), None)
    if existing:
        return {"detected": True, "interview": serialize_interview(existing), "reused": True}
    if not settings.TENCENT_MAAS_API_KEY.strip():
        raise HrServiceError("未配置腾讯云 MaaS API Key", 503)
    job = await get_job_by_id(db, workspace.job_id)
    input_hash = hashlib.sha256(f"{workspace.id}:{source.id}:{source.content}".encode()).hexdigest()
    task = AITask(
        id=str(uuid.uuid4()), user_id=user_id, task_type="hr_interview_detection",
        resource_type="hr_workspace", resource_id=workspace.id,
        status="generating", progress=30, model_name=settings.HR_ASSISTANT_MODEL,
        prompt_version=settings.HR_INTERVIEW_PROMPT_VERSION, input_hash=input_hash,
        request_payload={"workspace_id": workspace.id, "message_id": source.id},
        provider_call_started_at=utc_now_naive(), started_at=utc_now_naive(),
    )
    await create_ai_task(db, task); await db.commit()
    try:
        now_cn = datetime.now(resolve_timezone("Asia/Shanghai"))
        state = await HrInterviewAgent().run(
            current_time=now_cn.isoformat(timespec="seconds"), message=source.content,
            job={"title": job.title, "company": job.company} if job else {},
        )
        result = state["result"]
        usage = state.get("token_usage") or {}
        prompt = int(usage.get("prompt_tokens") or 0); completion = int(usage.get("completion_tokens") or 0)
        task.model_name = state.get("used_model_name") or settings.HR_ASSISTANT_MODEL
        task.token_usage = {"prompt_tokens": prompt, "completion_tokens": completion,
                            "total_tokens": int(usage.get("total_tokens") or prompt + completion),
                            "usage_reported": bool(usage)}
        if not result.has_interview_invitation:
            task.status, task.progress, task.finished_at = "success", 100, utc_now_naive()
            await db.commit()
            return {"detected": False, "interview": None, "ai_task_id": task.id}
        evidence = (result.evidence or "").strip()
        if not evidence or evidence not in source.content:
            raise HrServiceError("AI未提供可在HR原文中核验的面试证据", 422)
        scheduled_at = parse_ai_interview_time(result.scheduled_at)
        end_at = parse_ai_interview_time(result.end_at)
        missing = list(dict.fromkeys(result.missing_fields))
        if scheduled_at is None and "scheduled_at" not in missing:
            missing.append("scheduled_at")
        if scheduled_at is not None and scheduled_at <= utc_now_naive():
            scheduled_at = None
            if "scheduled_at" not in missing:
                missing.append("scheduled_at")
        if end_at is not None and (scheduled_at is None or end_at <= scheduled_at):
            end_at = None
            if "end_at" not in missing:
                missing.append("end_at")
        meeting_url = result.meeting_url
        if meeting_url and (not meeting_url.startswith("https://") or meeting_url not in source.content):
            meeting_url = None
            if "meeting_url" not in missing:
                missing.append("meeting_url")
        location = result.location if result.location and result.location in source.content else None
        if result.location and location is None and "location" not in missing:
            missing.append("location")
        interview_type = (
            result.interview_type
            if result.interview_type and result.interview_type in source.content else None
        )
        if result.interview_type and interview_type is None and "interview_type" not in missing:
            missing.append("interview_type")
        contact_name = (
            result.contact_name
            if result.contact_name and result.contact_name in source.content else None
        )
        if result.contact_name and contact_name is None and "contact_name" not in missing:
            missing.append("contact_name")
        required_missing = required_interview_fields_missing(
            scheduled_at=scheduled_at,
            interview_type=interview_type,
            location=location,
            meeting_url=meeting_url,
        )
        for field in required_missing:
            if field not in missing:
                missing.append(field)
        confirmation_reply = None
        if not required_missing:
            confirmation_reply = build_interview_confirmation_reply(
                scheduled_at=scheduled_at,
                timezone_name=result.timezone or "Asia/Shanghai",
                interview_type=interview_type,
                location=location,
                meeting_url=meeting_url,
            )
        interview = await create_interview(db, HrInterview(
            workspace_id=workspace.id, user_id=user_id, source_message_id=source.id,
            status="proposed", scheduled_at=scheduled_at, end_at=end_at,
            timezone=result.timezone or "Asia/Shanghai", interview_type=interview_type,
            location=location, meeting_url=meeting_url, contact_name=contact_name,
            evidence=evidence, missing_fields=missing, suggested_reply=confirmation_reply,
            requires_confirmation=True,
        ))
        action = None
        if confirmation_reply:
            action = await attach_interview_confirmation(
                db, workspace=workspace, interview=interview,
                reply_content=confirmation_reply, ai_generated=True,
            )
        else:
            workspace.status, workspace.current_step = "interview_pending", "面试信息不完整，请用户补充"
        task.status, task.progress, task.result_id = "success", 100, interview.id
        task.finished_at = utc_now_naive()
        await db.commit()
        return {"detected": True, "interview": serialize_interview(interview),
                "action_id": action.id if action else None, "ai_task_id": task.id, "reused": False}
    except Exception as exc:
        task.status, task.progress, task.finished_at = "failed", 100, utc_now_naive()
        task.error_message = (str(exc).strip() or "面试邀请识别失败")[:500]
        await db.commit()
        if isinstance(exc, HrServiceError):
            raise
        raise HrServiceError(task.error_message, 502) from exc


async def create_interview_proposal(
    db: AsyncSession, *, user_id: int, workspace_id: int, request: HrInterviewCreateRequest
) -> dict:
    workspace = await get_owned_workspace(db, workspace_id, user_id)
    if not workspace:
        raise HrServiceError("HR工作区不存在", 404)
    if workspace.status in ("completed", "cancelled"):
        raise HrServiceError("已结束的工作区不能创建面试安排", 409)
    await ensure_workspace_login(db, workspace)
    scheduled_at = to_utc_naive(request.scheduled_at)
    if scheduled_at <= utc_now_naive():
        raise HrServiceError("面试时间必须晚于当前时间", 422)
    interview = await create_interview(db, HrInterview(
        workspace_id=workspace.id, user_id=user_id, status="proposed",
        scheduled_at=scheduled_at,
        end_at=to_utc_naive(request.end_at) if request.end_at else None,
        timezone=request.timezone, interview_type=request.interview_type,
        location=request.location, meeting_url=request.meeting_url,
        contact_name=request.contact_name, evidence="用户手动填写并待确认",
        missing_fields=[], suggested_reply=request.reply_content,
        requires_confirmation=True,
    ))
    action = await attach_interview_confirmation(
        db, workspace=workspace, interview=interview, reply_content=request.reply_content,
        ai_generated=False,
    )
    await db.commit()
    return {"interview": serialize_interview(interview), "action_id": action.id}


async def get_workspace_interviews(db: AsyncSession, *, user_id: int, workspace_id: int) -> dict:
    if not await get_owned_workspace(db, workspace_id, user_id):
        raise HrServiceError("HR工作区不存在", 404)
    items = await list_interviews(db, workspace_id, user_id)
    return {"items": [serialize_interview(item) for item in items], "total": len(items)}


async def get_upcoming_interviews(db: AsyncSession, *, user_id: int) -> dict:
    items = list((await db.scalars(select(HrInterview).where(
        HrInterview.user_id == user_id, HrInterview.status == "scheduled",
        HrInterview.scheduled_at >= utc_now_naive(),
    ).order_by(HrInterview.scheduled_at.asc()))).all())
    return {"items": [serialize_interview(item) for item in items], "total": len(items)}


async def run_workspace_monitor_cycle(workspace_id: int) -> bool:
    """Run one durable HR automation cycle; return False when monitoring should stop."""
    from app.core.database import async_session

    async with async_session() as db:
        workspace = await get_workspace(db, workspace_id)
        if not workspace:
            return False
        permissions = workspace.permissions or {}
        if (
            workspace.automation_mode != "full_auto"
            or workspace.status in ("paused", "completed", "cancelled", "failed")
            or not (
                bool(permissions.get("auto_reply"))
                or bool(permissions.get("auto_schedule_interview"))
            )
        ):
            return False
        try:
            await sync_workspace_messages(
                db, user_id=workspace.user_id, workspace_id=workspace.id
            )
        except HrServiceError:
            refreshed = await get_workspace(db, workspace_id)
            return bool(refreshed and refreshed.status not in (
                "paused", "completed", "cancelled", "failed"
            ))
        return True


async def process_workspace_automation(
    db: AsyncSession, *, workspace: HrWorkspace
) -> dict:
    """Process the latest unanswered HR message exactly through the backend path."""
    permissions = workspace.permissions or {}
    if (
        workspace.automation_mode != "full_auto"
        or workspace.status in ("paused", "completed", "cancelled", "failed")
    ):
        return {"automation_action": None}
    messages = await list_messages(db, workspace.id, workspace.user_id)
    if not messages or messages[-1].sender_type != "hr":
        return {"automation_action": None}

    if permissions.get("auto_schedule_interview"):
        detection = await detect_interview_invitation(
            db,
            user_id=workspace.user_id,
            workspace_id=workspace.id,
            request=HrInterviewDetectRequest(message_id=messages[-1].id),
        )
        if detection.get("detected"):
            return {
                "automation_action": "interview_confirmation_required",
                "interview_detected": True,
            }

    if permissions.get("auto_reply"):
        suggestions = await generate_reply_suggestions(
            db, user_id=workspace.user_id, workspace_id=workspace.id
        )
        first = next(iter(suggestions.get("items") or []), None)
        if first and str(first.get("content") or "").strip():
            result = await create_outgoing_message(
                db,
                user_id=workspace.user_id,
                workspace_id=workspace.id,
                request=HrMessageSendRequest(
                    content=str(first["content"]).strip(),
                    send_mode="ai_suggestion",
                ),
            )
            return {
                "automation_action": (
                    "reply_confirmation_required"
                    if result["waiting_confirmation"]
                    else "reply_queued"
                ),
                "action_id": result["action_id"],
            }
    return {"automation_action": None}


async def hr_monitor_scheduler() -> None:
    """Continuously monitor every active full-auto workspace while FastAPI is running."""
    from app.core.database import async_session

    interval = max(15, int(getattr(settings, "HR_MONITOR_INTERVAL_SECONDS", 30)))
    failure_backoff = max(
        interval,
        int(getattr(settings, "HR_MONITOR_FAILURE_BACKOFF_SECONDS", 300)),
    )
    while True:
        try:
            async with async_session() as db:
                workspace_ids = list((await db.scalars(
                    select(HrWorkspace.id).where(
                        HrWorkspace.automation_mode == "full_auto",
                        HrWorkspace.status.in_((
                            "applied", "communicating",
                            "interview_pending", "interview_scheduled",
                        )),
                        or_(
                            HrWorkspace.sync_status != "failed",
                            HrWorkspace.sync_status.is_(None),
                            HrWorkspace.last_synced_at.is_(None),
                            HrWorkspace.last_synced_at
                            < utc_now_naive() - timedelta(seconds=failure_backoff),
                        ),
                    )
                )).all())
            for workspace_id in workspace_ids:
                try:
                    await run_workspace_monitor_cycle(int(workspace_id))
                except Exception:
                    # A single platform page must not stop monitoring other workspaces.
                    continue
        finally:
            await asyncio.sleep(interval)


async def execute_hr_interview_action(action_id: int) -> None:
    from app.core.database import async_session
    async with async_session() as db:
        action = await get_action(db, action_id)
        workspace = await get_workspace(db, action.workspace_id) if action else None
        payload = action.payload or {} if action else {}
        interview = await get_interview(db, int(payload.get("interview_id") or 0))
        message = await get_message(db, int(payload.get("message_id") or 0))
        if not action or not workspace or not interview or not message or action.status != "pending":
            return
        job = await get_job_by_id(db, workspace.job_id)
        try:
            session = await ensure_workspace_login(db, workspace)
        except HrServiceError as exc:
            await db.rollback(); await _mark_action_failed(
                action_id, exc.message, login_expired=True, session_id=workspace.login_session_id
            ); return
        if not job:
            await db.rollback(); await _mark_action_failed(action_id, "岗位不存在"); return
        action.status, message.status = "executing", "sending"
        await db.commit()
        context = {"storage_state": session.storage_state_ref, "source_url": job.source_url,
                   "thread_url": workspace.platform_thread_url, "expected_title": job.title,
                   "expected_source_id": job.source_id,
                   "content": action.content, "session_id": session.id}
    try:
        result = await send_message_58(**{k: context[k] for k in (
            "storage_state", "source_url", "thread_url", "expected_title",
            "expected_source_id", "content"
        )})
        async with async_session() as db:
            action = await get_action(db, action_id)
            workspace = await get_workspace(db, action.workspace_id) if action else None
            payload = action.payload or {} if action else {}
            interview = await get_interview(db, int(payload.get("interview_id") or 0))
            message = await get_message(db, int(payload.get("message_id") or 0))
            if not action or not workspace or not interview or not message:
                return
            now = utc_now_naive()
            action.status, action.executed_at, action.error_message = "success", now, None
            action.payload = {**payload, "platform_evidence": result["evidence"]}
            message.status, message.sent_at = "sent", now
            interview.status, interview.confirmed_at = "scheduled", now
            workspace.platform_thread_url = (
                result.get("thread_url") or workspace.platform_thread_url
            )
            workspace.status, workspace.current_step = "interview_scheduled", "面试已由用户确认"
            workspace.last_message, workspace.last_message_at = message.content[:500], now
            workspace.error_message = None
            await add_log(db, workspace_id=workspace.id, user_id=workspace.user_id,
                          action="interview_scheduled", description="平台已核验面试确认消息发送成功",
                          status="success")
            await db.commit()
    except PlatformLoginExpired as exc:
        await _mark_action_failed(action_id, str(exc), login_expired=True, session_id=context["session_id"])
    except Exception as exc:
        await _mark_action_failed(action_id, str(exc)[:500] or "面试确认发送失败")


def serialize_action(action: HrPendingAction) -> dict:
    return {"id": action.id, "action_type": action.action_type, "status": action.status,
            "content": action.content, "reason": action.reason,
            "payload": action.payload,
            "requires_confirmation": action.requires_confirmation,
            "error_message": action.error_message, "created_at": action.created_at,
            "approved_at": action.approved_at, "executed_at": action.executed_at}


def serialize_workspace(
    workspace: HrWorkspace, job: Job | None = None, actions: list | None = None,
    platform_login_status: str | None = None,
) -> dict:
    data = {"id": workspace.id, "job_id": workspace.job_id, "source": workspace.source,
            "resume_id": workspace.resume_id, "resume_source": workspace.resume_source,
            "resume_optimization_id": workspace.resume_optimization_id,
            "automation_mode": workspace.automation_mode, "permissions": workspace.permissions,
            "status": workspace.status, "progress": workspace.progress,
            "current_step": workspace.current_step, "ai_task_id": workspace.ai_task_id,
            "hr_name": workspace.hr_name,
            "unread_count": workspace.unread_count,
            "pending_confirmation_count": workspace.pending_confirmation_count,
            "last_message": workspace.last_message, "error_message": workspace.error_message,
            "last_message_at": workspace.last_message_at,
            "platform_login_status": platform_login_status or "unknown",
            "sync_status": workspace.sync_status,
            "sync_error": workspace.sync_error,
            "last_synced_at": workspace.last_synced_at,
            "platform_snapshot": workspace.platform_snapshot,
            "applied_at": workspace.applied_at, "created_at": workspace.created_at,
            "updated_at": workspace.updated_at, "interview": None}
    if job:
        salary = None
        if job.salary_min is not None or job.salary_max is not None:
            low = f"{job.salary_min / 1000:g}k" if job.salary_min is not None else "面议"
            high = f"{job.salary_max / 1000:g}k" if job.salary_max is not None else "面议"
            salary = f"{low}-{high}"
        data.update({"job_title": job.title, "company": job.company, "city": job.city,
                     "salary": salary, "source_name": job.source_name,
                     "source_url": job.source_url})
        data["job"] = {"id": job.id, "title": job.title, "company": job.company,
                       "city": job.city, "source_url": job.source_url}
    if actions is not None:
        data["actions"] = [serialize_action(item) for item in actions]
        data["pending_actions"] = [
            serialize_action(item) for item in actions
            if item.status == "waiting_confirmation"
        ]
    return data


async def workspace_detail(db: AsyncSession, *, user_id: int, workspace_id: int) -> dict:
    workspace = await get_owned_workspace(db, workspace_id, user_id)
    if not workspace: raise HrServiceError("HR工作区不存在", 404)
    try:
        session = await ensure_workspace_login(db, workspace)
        login_status = session.status
    except HrServiceError:
        session = (await db.execute(select(JobPlatformLoginSession).where(
            JobPlatformLoginSession.id == workspace.login_session_id
        ))).scalar_one_or_none()
        login_status = session.status if session else "not_logged_in"
    data = serialize_workspace(workspace, await get_job_by_id(db, workspace.job_id),
                               await list_workspace_actions(db, workspace.id, user_id), login_status)
    interview = await get_latest_interview(db, workspace.id, user_id)
    data["interview"] = serialize_interview(interview) if interview else None
    return data


async def workspace_list(db: AsyncSession, *, user_id: int, status: str | None, page: int, page_size: int) -> dict:
    rows, total = await list_workspaces(db, user_id=user_id, status=status, page=page, page_size=page_size)
    items = []
    for workspace, job in rows:
        session = (await db.execute(select(JobPlatformLoginSession).where(
            JobPlatformLoginSession.id == workspace.login_session_id
        ))).scalar_one_or_none()
        login_status = session.status if session else "not_logged_in"
        items.append(serialize_workspace(workspace, job, platform_login_status=login_status))
    return {"items": items,
            "total": total, "page": page, "page_size": page_size}


async def overview(db: AsyncSession, *, user_id: int) -> dict:
    return await count_workspace_overview(db, user_id)


async def workspace_logs(db: AsyncSession, *, user_id: int, workspace_id: int) -> dict:
    if not await get_owned_workspace(db, workspace_id, user_id): raise HrServiceError("HR工作区不存在", 404)
    items = [{"id": item.id, "action": item.action, "description": item.description,
              "status": item.status, "created_at": item.created_at}
             for item in await list_logs(db, workspace_id, user_id)]
    return {"items": items, "total": len(items)}
