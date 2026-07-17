"""HR assistant phase-one API."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
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
from app.services.hr_service import (
    HrServiceError,
    build_preflight,
    confirm_action,
    control_workspace,
    create_outgoing_message,
    create_interview_proposal,
    detect_interview_invitation,
    generate_reply_suggestions,
    get_workspace_messages,
    get_upcoming_interviews,
    get_workspace_interviews,
    overview,
    serialize_workspace,
    start_workspace,
    sync_workspace_messages,
    update_workspace_mode,
    workspace_detail,
    workspace_list,
    workspace_logs,
)


router = APIRouter(prefix="/api/hr", tags=["HR助手"])


def response(data, message: str = "success", code: int = 200) -> dict:
    return {"code": code, "message": message, "data": data}


def translate_error(exc: HrServiceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/automation/overview")
async def get_overview(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return response(await overview(db, user_id=current_user.id))


@router.get("/automation/preflight")
async def get_preflight(
    job_id: int = Query(gt=0), source: str = Query("58"),
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    if source != "58": raise HTTPException(status_code=422, detail="第一阶段仅支持58同城")
    return response(await build_preflight(db, user_id=current_user.id, job_id=job_id, source=source))


@router.post("/workspaces", status_code=status.HTTP_202_ACCEPTED)
async def create_hr_workspace(
    body: HrWorkspaceCreateRequest, current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        workspace, created = await start_workspace(db, user_id=current_user.id, request=body)
        return response(serialize_workspace(workspace), "AI投递说明生成任务已启动" if created else "返回已有工作区")
    except HrServiceError as exc: raise translate_error(exc) from exc


@router.get("/workspaces")
async def get_workspaces(
    workspace_status: str | None = Query(None, alias="status"), page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100), current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return response(await workspace_list(db, user_id=current_user.id, status=workspace_status, page=page, page_size=page_size))


@router.get("/workspaces/{workspace_id}")
async def get_workspace_detail(
    workspace_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    try: return response(await workspace_detail(db, user_id=current_user.id, workspace_id=workspace_id))
    except HrServiceError as exc: raise translate_error(exc) from exc


@router.post("/workspaces/{workspace_id}/actions/{action_id}/confirm")
async def confirm_workspace_action(
    workspace_id: int, action_id: int, body: HrActionConfirmRequest,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    try:
        workspace = await confirm_action(db, user_id=current_user.id, workspace_id=workspace_id,
                                         action_id=action_id, request=body)
        return response(serialize_workspace(workspace), "已确认并开始执行" if body.approved else "已拒绝本次操作")
    except HrServiceError as exc: raise translate_error(exc) from exc


@router.get("/workspaces/{workspace_id}/logs")
async def get_workspace_logs(
    workspace_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    try: return response(await workspace_logs(db, user_id=current_user.id, workspace_id=workspace_id))
    except HrServiceError as exc: raise translate_error(exc) from exc


@router.patch("/workspaces/{workspace_id}/mode")
async def patch_workspace_mode(
    workspace_id: int, body: HrWorkspaceModeRequest,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    try:
        return response(await update_workspace_mode(
            db, user_id=current_user.id, workspace_id=workspace_id, request=body
        ), "工作区模式已更新")
    except HrServiceError as exc: raise translate_error(exc) from exc


@router.post("/workspaces/{workspace_id}/control")
async def post_workspace_control(
    workspace_id: int, body: HrWorkspaceControlRequest,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    try:
        return response(await control_workspace(
            db, user_id=current_user.id, workspace_id=workspace_id, request=body
        ), "工作区状态已更新")
    except HrServiceError as exc: raise translate_error(exc) from exc


@router.get("/workspaces/{workspace_id}/messages")
async def get_messages(
    workspace_id: int, current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return response(await get_workspace_messages(
            db, user_id=current_user.id, workspace_id=workspace_id
        ))
    except HrServiceError as exc: raise translate_error(exc) from exc


@router.post("/workspaces/{workspace_id}/reply-suggestions")
async def post_reply_suggestions(
    workspace_id: int, current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return response(await generate_reply_suggestions(
            db, user_id=current_user.id, workspace_id=workspace_id
        ))
    except HrServiceError as exc: raise translate_error(exc) from exc


@router.post("/workspaces/{workspace_id}/messages/sync")
async def sync_messages(
    workspace_id: int, current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return response(await sync_workspace_messages(
            db, user_id=current_user.id, workspace_id=workspace_id
        ), "平台消息同步完成")
    except HrServiceError as exc: raise translate_error(exc) from exc


@router.post("/workspaces/{workspace_id}/messages", status_code=status.HTTP_202_ACCEPTED)
async def post_message(
    workspace_id: int, body: HrMessageSendRequest,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    try:
        return response(await create_outgoing_message(
            db, user_id=current_user.id, workspace_id=workspace_id, request=body
        ), "消息已进入发送流程")
    except HrServiceError as exc: raise translate_error(exc) from exc


@router.post("/workspaces/{workspace_id}/interviews/detect")
async def detect_interview(
    workspace_id: int, body: HrInterviewDetectRequest,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    try:
        return response(await detect_interview_invitation(
            db, user_id=current_user.id, workspace_id=workspace_id, request=body
        ), "面试邀请识别完成")
    except HrServiceError as exc: raise translate_error(exc) from exc


@router.post("/workspaces/{workspace_id}/interviews")
async def create_interview(
    workspace_id: int, body: HrInterviewCreateRequest,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    try:
        return response(await create_interview_proposal(
            db, user_id=current_user.id, workspace_id=workspace_id, request=body
        ), "面试安排已进入待确认状态")
    except HrServiceError as exc: raise translate_error(exc) from exc


@router.get("/workspaces/{workspace_id}/interviews")
async def list_workspace_interviews(
    workspace_id: int, current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return response(await get_workspace_interviews(
            db, user_id=current_user.id, workspace_id=workspace_id
        ))
    except HrServiceError as exc: raise translate_error(exc) from exc


@router.get("/interviews/upcoming")
async def list_upcoming_interviews(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    return response(await get_upcoming_interviews(db, user_id=current_user.id))
