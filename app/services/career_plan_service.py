"""Career planning upload, task orchestration and generation service."""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.career_planning_agent import CareerPlanningAgent
from app.core.config import settings
from app.crud.ai_task import (
    claim_provider_call,
    count_active_tasks_for_user,
    create_ai_task,
    get_ai_task,
    update_ai_task,
)
from app.crud.career_plan import (
    create_plan,
    create_profile,
    create_project_attachment,
    delete_project_attachment,
    get_plan_by_task,
    get_profile,
    get_project_attachment,
    get_project_attachments,
)
from app.models.ai import AITask
from app.models.career_plan import CareerPlan, CareerPlanningProfile, CareerProjectAttachment
from app.schemas.career_plan import CareerPlanCreateRequest, CareerPlanningProfileRequest
from app.workers.process_launcher import WorkerLaunchError, launch_ai_task_worker


ALLOWED_PROJECT_FILE_TYPES = {"pdf", "docx", "txt"}
MAX_PROJECT_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CareerPlanError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(slots=True)
class CareerPlanTaskStartResult:
    task: AITask
    plan: CareerPlan


def serialize_attachment(attachment: CareerProjectAttachment) -> dict:
    return {
        "id": attachment.id,
        "original_filename": attachment.original_filename,
        "file_type": attachment.file_type,
        "file_size": attachment.file_size,
        "status": attachment.status,
        "error_message": attachment.error_message,
    }


def serialize_profile(profile: CareerPlanningProfile) -> dict:
    return {
        "id": profile.id,
        "education": profile.education,
        "experience": profile.experience,
        "skills": profile.skills or [],
        "work_description": profile.work_description,
        "weekly_learning_hours": profile.weekly_learning_hours,
        "preferred_target_role": profile.preferred_target_role,
        "projects": profile.projects or [],
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


def serialize_plan(plan: CareerPlan) -> dict:
    return {
        "id": plan.id,
        "profile_id": plan.profile_id,
        "career_profile_summary": plan.career_profile_summary or {},
        "recommended_roles": plan.recommended_roles or [],
        "career_goals": plan.career_goals or {
            "short_term": [],
            "medium_term": [],
            "long_term": [],
        },
        "skill_gap_analysis": plan.skill_gap_analysis or [],
        "learning_path": plan.learning_path or {
            "total_weeks": 0,
            "hours_per_week": 0,
            "stages": [],
        },
        "action_plan": plan.action_plan or {
            "this_week": [],
            "this_month": [],
            "portfolio_projects": [],
            "resume_actions": [],
            "review_points": [],
        },
        "risks_and_alternatives": plan.risks_and_alternatives or {
            "risks": [],
            "assumptions_to_confirm": [],
            "alternative_roles": [],
            "adjustment_advice": [],
        },
        "retrieval_source": plan.retrieval_source,
        "retrieval_error": plan.retrieval_error,
        "retrieved_chunk_ids": plan.retrieved_chunk_ids or [],
        "knowledge_base_version": plan.knowledge_base_version,
        "created_at": plan.created_at,
    }


async def upload_project_attachment(
    db: AsyncSession,
    *,
    user_id: int,
    file: UploadFile,
) -> CareerProjectAttachment:
    if not file.filename:
        raise CareerPlanError("文件名不能为空", 400)
    suffix = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in ALLOWED_PROJECT_FILE_TYPES:
        raise CareerPlanError("仅支持 PDF、DOCX、TXT 项目附件", 400)

    content = await file.read()
    if not content:
        raise CareerPlanError("项目附件不能为空", 400)
    if len(content) > MAX_PROJECT_FILE_SIZE:
        raise CareerPlanError("项目附件大小超过限制", 400)

    user_dir = (Path(settings.UPLOAD_DIR).resolve() / "career_projects" / str(user_id)).resolve()
    user_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"career_project_{user_id}_{uuid.uuid4().hex}.{suffix}"
    file_path = (user_dir / stored_filename).resolve()
    if file_path.parent != user_dir:
        raise CareerPlanError("无效的文件路径", 400)
    file_path.write_bytes(content)

    status = "completed"
    error_message = None
    extracted_text = ""
    try:
        extracted_text = extract_project_file_text(file_path, suffix)
    except Exception as exc:
        status = "failed"
        error_message = f"附件文本提取失败: {str(exc)[:450]}"

    attachment = CareerProjectAttachment(
        user_id=user_id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=str(file_path),
        file_type=suffix,
        file_size=len(content),
        extracted_text=extracted_text,
        status=status,
        error_message=error_message,
    )
    return await create_project_attachment(db, attachment)


def extract_project_file_text(file_path: Path, file_type: str) -> str:
    if file_type == "txt":
        raw = file_path.read_bytes()
        for encoding in ("utf-8", "utf-8-sig", "gbk"):
            try:
                return raw.decode(encoding).strip()
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="ignore").strip()
    if file_type == "pdf":
        import pdfplumber

        with pdfplumber.open(str(file_path)) as pdf:
            return "\n".join((page.extract_text() or "") for page in pdf.pages).strip()
    if file_type == "docx":
        from docx import Document

        doc = Document(str(file_path))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs).strip()
    return ""


async def remove_project_attachment(
    db: AsyncSession,
    *,
    user_id: int,
    file_id: int,
) -> None:
    attachment = await get_project_attachment(db, file_id, user_id)
    if attachment is None:
        raise CareerPlanError("项目附件不存在", 404)
    try:
        path = Path(attachment.file_path).resolve()
        user_dir = (Path(settings.UPLOAD_DIR).resolve() / "career_projects" / str(user_id)).resolve()
        if path.parent == user_dir and path.exists() and path.is_file():
            path.unlink()
    finally:
        await delete_project_attachment(db, attachment)


async def create_career_profile(
    db: AsyncSession,
    *,
    user_id: int,
    request: CareerPlanningProfileRequest,
) -> CareerPlanningProfile:
    file_ids = sorted({file_id for project in request.projects for file_id in project.file_ids})
    attachments = await get_project_attachments(db, file_ids, user_id)
    found_ids = {item.id for item in attachments}
    missing_ids = [file_id for file_id in file_ids if file_id not in found_ids]
    if missing_ids:
        raise CareerPlanError(f"项目附件不存在或无权访问: {missing_ids}", 404)

    profile = CareerPlanningProfile(
        user_id=user_id,
        education=request.education,
        experience=request.experience,
        skills=request.skills,
        work_description=request.work_description,
        weekly_learning_hours=request.weekly_learning_hours,
        preferred_target_role=request.preferred_target_role,
        projects=[project.model_dump(mode="json") for project in request.projects],
    )
    return await create_profile(db, profile)


async def start_career_plan(
    db: AsyncSession,
    *,
    user_id: int,
    request: CareerPlanCreateRequest,
) -> CareerPlanTaskStartResult:
    profile = await get_profile(db, request.profile_id, user_id)
    if profile is None:
        raise CareerPlanError("职业规划档案不存在", 404)

    active_count = await count_active_tasks_for_user(db, user_id)
    if active_count >= settings.AI_MAX_CONCURRENT_TASKS:
        raise CareerPlanError("已有 AI 任务正在运行，请等待任务完成", 409)

    payload = request.model_dump(mode="json")
    input_hash = build_career_input_hash(profile, payload)
    plan = CareerPlan(
        user_id=user_id,
        profile_id=profile.id,
        status="processing",
        career_profile_summary={},
        recommended_roles=[],
        career_goals={"short_term": [], "medium_term": [], "long_term": []},
        skill_gap_analysis=[],
        learning_path={"total_weeks": 0, "hours_per_week": profile.weekly_learning_hours, "stages": []},
        action_plan={
            "this_week": [],
            "this_month": [],
            "portfolio_projects": [],
            "resume_actions": [],
            "review_points": [],
        },
        risks_and_alternatives={
            "risks": [],
            "assumptions_to_confirm": [],
            "alternative_roles": [],
            "adjustment_advice": [],
        },
        model_name=settings.CAREER_PLANNING_MODEL,
        prompt_version=settings.AI_PROMPT_VERSION,
    )
    await create_plan(db, plan)

    task = AITask(
        id=str(uuid.uuid4()),
        user_id=user_id,
        task_type="career_plan",
        resource_type="career_plan",
        resource_id=plan.id,
        status="pending",
        progress=0,
        model_name=settings.CAREER_PLANNING_MODEL,
        prompt_version=settings.AI_PROMPT_VERSION,
        input_hash=input_hash,
        request_payload=payload,
    )
    await create_ai_task(db, task)
    plan.task_id = task.id
    await db.flush()
    # The worker uses a separate database session, so the task must be visible
    # before the process starts.
    await db.commit()

    try:
        launch_ai_task_worker(task.id)
    except WorkerLaunchError as exc:
        task.status = "failed"
        task.progress = 100
        task.error_message = "无法启动职业规划 worker，请稍后重试"
        task.finished_at = utc_now_naive()
        plan.status = "failed"
        plan.error_message = task.error_message
        await db.commit()
        raise CareerPlanError(task.error_message, 503) from exc

    return CareerPlanTaskStartResult(task=task, plan=plan)


def build_career_input_hash(profile: CareerPlanningProfile, payload: dict) -> str:
    source = {
        "user_id": profile.user_id,
        "profile_id": profile.id,
        "education": profile.education,
        "experience": profile.experience,
        "skills": profile.skills,
        "work_description": profile.work_description,
        "weekly_learning_hours": profile.weekly_learning_hours,
        "preferred_target_role": profile.preferred_target_role,
        "projects": profile.projects,
        "payload": payload,
        "prompt_version": settings.AI_PROMPT_VERSION,
    }
    serialized = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


async def execute_career_plan_task(task_id: str) -> None:
    from app.core.database import async_session

    async with async_session() as db:
        task = await get_ai_task(db, task_id)
        if task is None or task.status != "pending":
            return
        task.status = "preparing"
        task.progress = 10
        task.started_at = utc_now_naive()
        await db.commit()

    try:
        async with async_session() as db:
            task = await get_ai_task(db, task_id)
            if task is None:
                return
            plan = await get_plan_by_task(db, task.id)
            if plan is None:
                raise CareerPlanError("职业规划记录不存在", 404)
            profile = await get_profile(db, plan.profile_id, task.user_id)
            if profile is None:
                raise CareerPlanError("职业规划档案不存在", 404)
            attachment_ids = sorted({
                file_id
                for project in profile.projects or []
                if isinstance(project, dict)
                for file_id in (project.get("file_ids") or [])
            })
            attachments = await get_project_attachments(db, attachment_ids, task.user_id)
            profile_payload = serialize_profile_for_agent(profile)
            attachment_payload = serialize_attachments_for_agent(attachments)
            if not settings.TENCENT_MAAS_API_KEY.strip():
                raise CareerPlanError("未配置腾讯云 MaaS API Key", 503)
            await claim_provider_call(db, task, utc_now_naive())
            task.status = "generating"
            task.progress = 35
            plan.status = "processing"
            await db.commit()

        result, token_usage, generation_audit = await build_generated_career_plan(
            profile_payload=profile_payload,
            project_attachments=attachment_payload,
            request_payload=task.request_payload or {},
        )

        async with async_session() as db:
            task = await get_ai_task(db, task_id)
            if task is None:
                return
            plan = await get_plan_by_task(db, task.id)
            if plan is None:
                return
            task.status = "validating"
            task.progress = 75
            task.token_usage = token_usage or {}
            await db.flush()
            normalized = normalize_generated_plan(result, plan)
            task.status = "saving"
            task.progress = 90
            plan.career_profile_summary = normalized["career_profile_summary"]
            plan.recommended_roles = normalized["recommended_roles"]
            plan.career_goals = normalized["career_goals"]
            plan.skill_gap_analysis = normalized["skill_gap_analysis"]
            plan.learning_path = normalized["learning_path"]
            plan.action_plan = normalized["action_plan"]
            plan.risks_and_alternatives = normalized["risks_and_alternatives"]
            plan.retrieval_source = generation_audit["retrieval_source"]
            plan.retrieval_error = generation_audit["retrieval_error"]
            plan.retrieved_chunk_ids = generation_audit["retrieved_chunk_ids"]
            plan.knowledge_base_version = generation_audit["knowledge_base_version"]
            plan.status = "completed"
            plan.error_message = None
            task.status = "success"
            task.progress = 100
            task.result_id = plan.id
            task.error_message = None
            task.finished_at = utc_now_naive()
            await db.commit()
    except Exception as exc:
        await mark_career_task_failed(task_id, safe_error_message(exc))
        raise


async def build_generated_career_plan(
    *,
    profile_payload: dict,
    project_attachments: list[dict],
    request_payload: dict,
) -> tuple[dict, dict, dict]:
    agent = CareerPlanningAgent()
    state = await agent.run(
        profile=profile_payload,
        project_attachments=project_attachments,
        request_payload=request_payload,
    )
    result = state["result"].model_dump(mode="json")
    raw_usage = state.get("token_usage") or {}
    prompt_tokens = int(raw_usage.get("prompt_tokens") or 0)
    completion_tokens = int(raw_usage.get("completion_tokens") or 0)
    token_usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": int(raw_usage.get("total_tokens") or prompt_tokens + completion_tokens),
        "usage_reported": bool(raw_usage),
    }
    chunks = state.get("knowledge_chunks") or []
    versions = sorted({chunk.version for chunk in chunks if chunk.version})
    generation_audit = {
        "retrieval_source": state.get("retrieval_source") or "unknown",
        "retrieval_error": state.get("retrieval_error"),
        "retrieved_chunk_ids": state.get("retrieved_chunk_ids") or [chunk.id for chunk in chunks],
        "knowledge_base_version": ",".join(versions)[:100] or None,
    }
    return result, token_usage, generation_audit


def normalize_generated_plan(plan: dict, plan_record: CareerPlan) -> dict:
    defaults = awaitable_defaults(plan_record)
    normalized = {**defaults, **(plan or {})}
    for key, value in defaults.items():
        if normalized.get(key) is None:
            normalized[key] = value
    return normalized


def awaitable_defaults(plan_record: CareerPlan) -> dict:
    return {
        "career_profile_summary": {
            "current_stage": "",
            "core_strengths": [],
            "transferable_skills": [],
            "main_weaknesses": [],
            "summary": "",
        },
        "recommended_roles": [],
        "career_goals": {"short_term": [], "medium_term": [], "long_term": []},
        "skill_gap_analysis": [],
        "learning_path": {"total_weeks": 12, "hours_per_week": 8, "stages": []},
        "action_plan": {
            "this_week": [],
            "this_month": [],
            "portfolio_projects": [],
            "resume_actions": [],
            "review_points": [],
        },
        "risks_and_alternatives": {
            "risks": [],
            "assumptions_to_confirm": [],
            "alternative_roles": [],
            "adjustment_advice": [],
        },
    }


def serialize_profile_for_agent(profile: CareerPlanningProfile) -> dict:
    return {
        "id": profile.id,
        "education": profile.education,
        "experience": profile.experience,
        "skills": profile.skills or [],
        "work_description": profile.work_description,
        "weekly_learning_hours": profile.weekly_learning_hours,
        "preferred_target_role": profile.preferred_target_role,
        "projects": profile.projects or [],
    }


def serialize_attachments_for_agent(attachments: list[CareerProjectAttachment]) -> list[dict]:
    return [
        {
            "id": item.id,
            "original_filename": item.original_filename,
            "file_type": item.file_type,
            "status": item.status,
            "error_message": item.error_message,
            "extracted_text": (item.extracted_text or "")[:4000],
        }
        for item in attachments
    ]


async def mark_career_task_failed(task_id: str, message: str) -> None:
    from app.core.database import async_session

    async with async_session() as db:
        task = await get_ai_task(db, task_id)
        if task is None or task.status in ("success", "cancelled"):
            return
        await update_ai_task(
            db,
            task_id,
            status="failed",
            progress=100,
            error_message=message[:500],
            finished_at=utc_now_naive(),
        )
        plan = await get_plan_by_task(db, task_id)
        if plan is not None:
            plan.status = "failed"
            plan.error_message = message[:500]
        await db.commit()


def safe_error_message(exc: Exception) -> str:
    if isinstance(exc, CareerPlanError):
        return str(exc)
    message = str(exc).strip()
    return message[:500] if message else "职业规划任务执行失败，请稍后重试"
