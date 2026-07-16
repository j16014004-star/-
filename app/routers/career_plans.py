"""Career planning endpoints."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.crud.career_plan import get_plan
from app.models.user import User
from app.schemas.career_plan import CareerPlanCreateRequest, CareerPlanningProfileRequest
from app.services.career_plan_service import (
    CareerPlanError,
    create_career_profile,
    remove_project_attachment,
    serialize_attachment,
    serialize_plan,
    serialize_profile,
    start_career_plan,
    upload_project_attachment,
)


profile_router = APIRouter(prefix="/api/career-planning", tags=["职业规划"])
plan_router = APIRouter(prefix="/api/career-plans", tags=["职业规划"])


def raise_career_error(exc: CareerPlanError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@plan_router.post("/project-files/upload")
async def upload_project_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        attachment = await upload_project_attachment(db, user_id=current_user.id, file=file)
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {
        "code": 200,
        "message": "success",
        "data": serialize_attachment(attachment),
    }


@plan_router.delete("/project-files/{file_id}")
async def delete_project_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await remove_project_attachment(db, user_id=current_user.id, file_id=file_id)
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {"code": 200, "message": "success", "data": None}


@profile_router.post("/profiles")
async def create_profile(
    body: CareerPlanningProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        profile = await create_career_profile(db, user_id=current_user.id, request=body)
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {
        "code": 200,
        "message": "success",
        "data": serialize_profile(profile),
    }


@plan_router.post("")
async def create_plan(
    body: CareerPlanCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await start_career_plan(db, user_id=current_user.id, request=body)
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "task_id": result.task.id,
            "status": result.task.status,
            "result_id": result.task.result_id,
            "plan_id": result.plan.id,
            "poll_after_seconds": 2,
        },
    }


@plan_router.get("/{plan_id}")
async def get_career_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan = await get_plan(db, plan_id, current_user.id)
    if plan is None:
        raise HTTPException(status_code=404, detail="职业规划不存在")
    return {
        "code": 200,
        "message": "success",
        "data": serialize_plan(plan),
    }
