"""Database access for HR assistant."""
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hr import HrActionLog, HrInterview, HrMessage, HrPendingAction, HrWorkspace
from app.models.job import Job, JobApplication


ACTIVE_WORKSPACE_STATUSES = (
    "draft", "applying", "applied", "communicating", "interview_pending",
    "interview_scheduled", "paused",
)


async def create_workspace(db: AsyncSession, workspace: HrWorkspace) -> HrWorkspace:
    db.add(workspace)
    await db.flush()
    await db.refresh(workspace)
    return workspace


async def get_owned_workspace(
    db: AsyncSession, workspace_id: int, user_id: int
) -> HrWorkspace | None:
    return (await db.execute(
        select(HrWorkspace).where(HrWorkspace.id == workspace_id, HrWorkspace.user_id == user_id)
    )).scalar_one_or_none()


async def get_workspace(db: AsyncSession, workspace_id: int) -> HrWorkspace | None:
    return (await db.execute(
        select(HrWorkspace).where(HrWorkspace.id == workspace_id)
    )).scalar_one_or_none()


async def get_existing_workspace(
    db: AsyncSession,
    *,
    user_id: int,
    job_id: int,
    resume_id: int,
    resume_source: str,
    resume_optimization_id: int | None,
) -> HrWorkspace | None:
    query = select(HrWorkspace).where(
        HrWorkspace.user_id == user_id,
        HrWorkspace.job_id == job_id,
        HrWorkspace.resume_id == resume_id,
        HrWorkspace.resume_source == resume_source,
        HrWorkspace.status.in_(ACTIVE_WORKSPACE_STATUSES),
    )
    if resume_optimization_id is None:
        query = query.where(HrWorkspace.resume_optimization_id.is_(None))
    else:
        query = query.where(HrWorkspace.resume_optimization_id == resume_optimization_id)
    return (await db.execute(query.order_by(HrWorkspace.created_at.desc()).limit(1))).scalar_one_or_none()


async def list_workspaces(
    db: AsyncSession,
    *,
    user_id: int,
    status: str | None,
    page: int,
    page_size: int,
) -> tuple[list[tuple[HrWorkspace, Job]], int]:
    conditions = [HrWorkspace.user_id == user_id]
    if status:
        conditions.append(HrWorkspace.status == status)
    total = int((await db.scalar(
        select(func.count(HrWorkspace.id)).where(*conditions)
    )) or 0)
    rows = list((await db.execute(
        select(HrWorkspace, Job)
        .join(Job, Job.id == HrWorkspace.job_id)
        .where(*conditions)
        .order_by(HrWorkspace.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).all())
    return rows, total


async def count_workspace_overview(db: AsyncSession, user_id: int) -> dict:
    total = int((await db.scalar(
        select(func.count(HrWorkspace.id)).where(HrWorkspace.user_id == user_id)
    )) or 0)
    active = int((await db.scalar(
        select(func.count(HrWorkspace.id)).where(
            HrWorkspace.user_id == user_id,
            HrWorkspace.status.in_(ACTIVE_WORKSPACE_STATUSES),
        )
    )) or 0)
    unread = int((await db.scalar(
        select(func.coalesce(func.sum(HrWorkspace.unread_count), 0)).where(
            HrWorkspace.user_id == user_id
        )
    )) or 0)
    pending = int((await db.scalar(
        select(func.count(HrPendingAction.id)).where(
            HrPendingAction.user_id == user_id,
            HrPendingAction.status == "waiting_confirmation",
        )
    )) or 0)
    upcoming = int((await db.scalar(select(func.count(HrInterview.id)).where(
        HrInterview.user_id == user_id,
        HrInterview.status == "scheduled",
        HrInterview.scheduled_at >= datetime.now(timezone.utc).replace(tzinfo=None),
    ))) or 0)
    return {
        "total_workspaces": total,
        "active_workspaces": active,
        "unread_messages": unread,
        "pending_confirmations": pending,
        "upcoming_interviews": upcoming,
    }


async def create_action(db: AsyncSession, action: HrPendingAction) -> HrPendingAction:
    db.add(action)
    await db.flush()
    await db.refresh(action)
    return action


async def get_owned_action(
    db: AsyncSession, action_id: int, workspace_id: int, user_id: int
) -> HrPendingAction | None:
    return (await db.execute(
        select(HrPendingAction).where(
            HrPendingAction.id == action_id,
            HrPendingAction.workspace_id == workspace_id,
            HrPendingAction.user_id == user_id,
        )
    )).scalar_one_or_none()


async def get_action(db: AsyncSession, action_id: int) -> HrPendingAction | None:
    return (await db.execute(
        select(HrPendingAction).where(HrPendingAction.id == action_id)
    )).scalar_one_or_none()


async def list_workspace_actions(
    db: AsyncSession, workspace_id: int, user_id: int
) -> list[HrPendingAction]:
    return list((await db.scalars(
        select(HrPendingAction)
        .where(
            HrPendingAction.workspace_id == workspace_id,
            HrPendingAction.user_id == user_id,
        )
        .order_by(HrPendingAction.created_at.desc())
    )).all())


async def add_log(
    db: AsyncSession,
    *,
    workspace_id: int,
    user_id: int,
    action: str,
    description: str,
    status: str,
) -> HrActionLog:
    item = HrActionLog(
        workspace_id=workspace_id,
        user_id=user_id,
        action=action[:100],
        description=description[:1000],
        status=status[:30],
    )
    db.add(item)
    await db.flush()
    return item


async def list_logs(
    db: AsyncSession, workspace_id: int, user_id: int
) -> list[HrActionLog]:
    return list((await db.scalars(
        select(HrActionLog)
        .where(HrActionLog.workspace_id == workspace_id, HrActionLog.user_id == user_id)
        .order_by(HrActionLog.created_at.desc())
    )).all())


async def get_existing_application(
    db: AsyncSession, *, user_id: int, job_id: int
) -> JobApplication | None:
    return (await db.execute(
        select(JobApplication)
        .where(JobApplication.user_id == user_id, JobApplication.job_id == job_id)
        .order_by(JobApplication.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()


async def create_message(db: AsyncSession, message: HrMessage) -> HrMessage:
    db.add(message)
    await db.flush()
    await db.refresh(message)
    return message


async def get_message(db: AsyncSession, message_id: int) -> HrMessage | None:
    return (await db.execute(
        select(HrMessage).where(HrMessage.id == message_id)
    )).scalar_one_or_none()


async def list_messages(db: AsyncSession, workspace_id: int, user_id: int) -> list[HrMessage]:
    return list((await db.scalars(
        select(HrMessage).where(
            HrMessage.workspace_id == workspace_id, HrMessage.user_id == user_id
        ).order_by(HrMessage.created_at.asc())
    )).all())


async def create_interview(db: AsyncSession, interview: HrInterview) -> HrInterview:
    db.add(interview)
    await db.flush()
    await db.refresh(interview)
    return interview


async def get_interview(db: AsyncSession, interview_id: int) -> HrInterview | None:
    return (await db.execute(
        select(HrInterview).where(HrInterview.id == interview_id)
    )).scalar_one_or_none()


async def get_owned_interview(
    db: AsyncSession, interview_id: int, workspace_id: int, user_id: int
) -> HrInterview | None:
    return (await db.execute(select(HrInterview).where(
        HrInterview.id == interview_id, HrInterview.workspace_id == workspace_id,
        HrInterview.user_id == user_id,
    ))).scalar_one_or_none()


async def list_interviews(db: AsyncSession, workspace_id: int, user_id: int) -> list[HrInterview]:
    return list((await db.scalars(select(HrInterview).where(
        HrInterview.workspace_id == workspace_id, HrInterview.user_id == user_id,
    ).order_by(HrInterview.scheduled_at.asc(), HrInterview.created_at.desc()))).all())


async def get_latest_interview(
    db: AsyncSession, workspace_id: int, user_id: int
) -> HrInterview | None:
    return (await db.execute(select(HrInterview).where(
        HrInterview.workspace_id == workspace_id, HrInterview.user_id == user_id,
    ).order_by(HrInterview.created_at.desc()).limit(1))).scalar_one_or_none()
