"""Career planning endpoints."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.crud.career_plan import get_plan
from app.models.user import User
from app.schemas.career_plan import (
    CareerPlanCreateRequest,
    CareerPlanRegenerateRequest,
    CareerPlanningProfileRequest,
    CareerQuestionRequest,
    CareerAssessmentSubmitRequest,
    CareerTaskCheckinRequest,
)
from app.services.career_execution_service import (
    accept_career_plan,
    check_in_execution_task,
    get_current_execution_overview,
    advance_execution_task,
)
from app.services.career_assessment_service import (
    activate_next_stage, create_remediation, create_stage_assessment,
    get_stage_assessment_detail, get_stage_assessment_result,
    submit_stage_assessment,
)
from app.services.career_plan_service import (
    CareerPlanError,
    create_career_profile,
    remove_project_attachment,
    regenerate_career_plan,
    serialize_attachment,
    serialize_plan,
    serialize_profile,
    start_career_plan,
    upload_project_attachment,
)
from app.services.career_question_service import (
    get_career_question_detail,
    list_career_questions,
    submit_career_question,
)


profile_router = APIRouter(prefix="/api/career-planning", tags=["职业规划"])
plan_router = APIRouter(prefix="/api/career-plans", tags=["职业规划"])
execution_router = APIRouter(prefix="/api/career-plan-executions", tags=["职业规划执行"])


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


@plan_router.post("/{plan_id}/accept")
async def accept_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        plan, execution = await accept_career_plan(db, user_id=current_user.id, plan_id=plan_id)
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "plan_id": plan.id,
            "status": "accepted",
            "accepted_at": plan.accepted_at,
            "execution_plan_id": execution.id,
        },
    }


@plan_router.post("/{plan_id}/regenerate")
async def regenerate_plan(
    plan_id: int,
    body: CareerPlanRegenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await regenerate_career_plan(
            db, user_id=current_user.id, plan_id=plan_id, request=body
        )
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
            "previous_plan_id": plan_id,
            "poll_after_seconds": 1,
        },
    }


@execution_router.get("/current")
async def get_current_execution(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        overview = await get_current_execution_overview(db, user_id=current_user.id)
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {"code": 200, "message": "success", "data": overview}


@execution_router.post("/tasks/{task_id}/check-in")
async def check_in_task(
    task_id: int,
    body: CareerTaskCheckinRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        overview = await check_in_execution_task(
            db, user_id=current_user.id, task_id=task_id, request=body
        )
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {"code": 200, "message": "success", "data": overview}


@execution_router.post("/{execution_plan_id}/advance")
async def advance_plan_task(execution_plan_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        data = await advance_execution_task(db, user_id=current_user.id, execution_plan_id=execution_plan_id)
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {"code": 200, "message": "success", "data": data}


@execution_router.post("/{execution_plan_id}/assessments")
async def create_assessment(execution_plan_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        data = await create_stage_assessment(db, user_id=current_user.id, execution_plan_id=execution_plan_id)
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {"code": 200, "message": "success", "data": data}


@execution_router.get("/assessments/{assessment_id}")
async def assessment_detail(assessment_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        data = await get_stage_assessment_detail(db, user_id=current_user.id, assessment_id=assessment_id)
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {"code": 200, "message": "success", "data": data}


@execution_router.post("/assessments/{assessment_id}/submit")
async def submit_assessment(assessment_id: int, body: CareerAssessmentSubmitRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        data = await submit_stage_assessment(db, user_id=current_user.id, assessment_id=assessment_id, request=body)
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {"code": 200, "message": "success", "data": data}


@execution_router.get("/assessments/{assessment_id}/result")
async def assessment_result(assessment_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        data = await get_stage_assessment_result(db, user_id=current_user.id, assessment_id=assessment_id)
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {"code": 200, "message": "success", "data": data}


@execution_router.post("/assessments/{assessment_id}/next-stage")
async def next_stage(assessment_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        data = await activate_next_stage(db, user_id=current_user.id, assessment_id=assessment_id)
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {"code": 200, "message": "success", "data": data}


@execution_router.post("/assessments/{assessment_id}/remediation")
async def remediation(assessment_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        data = await create_remediation(db, user_id=current_user.id, assessment_id=assessment_id)
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {"code": 200, "message": "success", "data": data}


@execution_router.post("/tasks/{execution_task_id}/questions")
async def create_task_question(
    execution_task_id: int,
    body: CareerQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await submit_career_question(
            db,
            user_id=current_user.id,
            execution_task_id=execution_task_id,
            request=body,
        )
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "task_id": result.task.id,
            "task_type": "career_plan_question",
            "status": result.task.status,
            "result_id": result.task.result_id,
            "question_id": result.question.id,
            "poll_after_seconds": 1,
        },
    }


@execution_router.get("/tasks/{execution_task_id}/questions")
async def get_task_question_history(
    execution_task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        questions = await list_career_questions(
            db, user_id=current_user.id, execution_task_id=execution_task_id
        )
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {"code": 200, "message": "success", "data": questions}


@execution_router.get("/questions/{question_id}")
async def get_question_detail(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        question = await get_career_question_detail(
            db, user_id=current_user.id, question_id=question_id
        )
    except CareerPlanError as exc:
        raise_career_error(exc)
    return {"code": 200, "message": "success", "data": question}


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
