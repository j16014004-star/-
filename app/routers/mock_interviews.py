"""Authenticated AI mock interview endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.mock_interview import MockInterviewAnswerRequest, MockInterviewCreateRequest
from app.services.mock_interview_service import (
    MockInterviewError,
    create_mock_interview,
    delete_mock_interview,
    finish_mock_interview,
    get_interview_options,
    get_mock_interview,
    get_mock_interview_report,
    get_next_question,
    list_mock_interviews,
    retry_weaknesses,
    serialize_interview,
    start_mock_interview,
    submit_mock_interview_answer,
)


router = APIRouter(prefix="/api/interviews", tags=["AI模拟面试"])


def ok(data=None, message: str = "success"):
    return {"code": 200, "message": message, "data": data}


def fail(exc: MockInterviewError):
    raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/options")
async def options(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    return ok(await get_interview_options(db, user_id=current_user.id))


@router.get("")
async def list_items(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    return ok(await list_mock_interviews(db, user_id=current_user.id))


@router.post("")
async def create_item(
    body: MockInterviewCreateRequest,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    try:
        item = await create_mock_interview(db, user_id=current_user.id, request=body)
    except MockInterviewError as exc:
        fail(exc)
    return ok(serialize_interview(item), "面试题已生成")


@router.get("/{interview_id}")
async def detail(
    interview_id: int, current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return ok(await get_mock_interview(db, user_id=current_user.id, interview_id=interview_id))
    except MockInterviewError as exc:
        fail(exc)


@router.post("/{interview_id}/start")
async def start(
    interview_id: int, current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return ok(await start_mock_interview(db, user_id=current_user.id, interview_id=interview_id))
    except MockInterviewError as exc:
        fail(exc)


@router.get("/{interview_id}/next-question")
async def next_question(
    interview_id: int, current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return ok(await get_next_question(db, user_id=current_user.id, interview_id=interview_id))
    except MockInterviewError as exc:
        fail(exc)


@router.post("/{interview_id}/answer")
async def answer(
    interview_id: int, body: MockInterviewAnswerRequest,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    try:
        return ok(await submit_mock_interview_answer(
            db, user_id=current_user.id, interview_id=interview_id, request=body
        ))
    except MockInterviewError as exc:
        fail(exc)


@router.post("/{interview_id}/finish")
async def finish(
    interview_id: int, current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return ok(await finish_mock_interview(db, user_id=current_user.id, interview_id=interview_id))
    except MockInterviewError as exc:
        fail(exc)


@router.get("/{interview_id}/report")
async def report(
    interview_id: int, current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return ok(await get_mock_interview_report(db, user_id=current_user.id, interview_id=interview_id))
    except MockInterviewError as exc:
        fail(exc)


@router.post("/{interview_id}/retry")
async def retry(
    interview_id: int, current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await retry_weaknesses(db, user_id=current_user.id, interview_id=interview_id)
    except MockInterviewError as exc:
        fail(exc)
    return ok(serialize_interview(item), "薄弱项复试已生成")


@router.delete("/{interview_id}")
async def remove(
    interview_id: int, current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await delete_mock_interview(db, user_id=current_user.id, interview_id=interview_id)
    except MockInterviewError as exc:
        fail(exc)
    return ok(None, "面试记录已删除")
