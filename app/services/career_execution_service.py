"""Acceptance, execution schedule and check-in services for career plans."""
from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.career_plan import (
    create_checkin,
    create_execution,
    create_execution_tasks,
    get_current_execution,
    get_execution_by_id,
    get_execution_by_plan,
    get_execution_tasks,
    get_owned_execution_task,
    get_plan,
    get_recent_checkins,
    pause_active_executions,
)
from app.models.career_plan import (
    CareerPlan,
    CareerPlanCheckin,
    CareerPlanExecution,
    CareerPlanExecutionTask,
    CareerStageProgress,
)
from app.models.user import User
from app.schemas.career_plan import CareerTaskCheckinRequest
from app.services.career_plan_service import CareerPlanError


CHINA_TZ = timezone(timedelta(hours=8))


def today_in_china() -> date:
    return datetime.now(CHINA_TZ).date()


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def accept_career_plan(
    db: AsyncSession, *, user_id: int, plan_id: int
) -> tuple[CareerPlan, CareerPlanExecution]:
    # Serialize accepts for the same user so two plans cannot become active concurrently.
    await db.execute(select(User.id).where(User.id == user_id).with_for_update())
    plan = await get_plan(db, plan_id, user_id)
    if plan is None:
        raise CareerPlanError("职业规划不存在", 404)
    if plan.status not in ("completed", "accepted"):
        raise CareerPlanError("职业规划尚未生成完成，不能确认采用", 409)

    existing = await get_execution_by_plan(db, plan.id, user_id)
    if plan.status == "accepted" and existing is not None:
        return plan, existing

    await pause_active_executions(db, user_id)
    accepted_at = plan.accepted_at or utc_now_naive()
    plan.status = "accepted"
    plan.accepted_at = accepted_at

    if existing is None:
        execution = CareerPlanExecution(
            user_id=user_id,
            career_plan_id=plan.id,
            status="active",
            start_date=today_in_china(),
        )
        await create_execution(db, execution)
    else:
        execution = existing
        execution.status = "active"
        execution.end_date = None

    tasks = await get_execution_tasks(db, execution.id, user_id)
    if not tasks:
        await create_execution_tasks(db, build_execution_tasks(plan, execution))
    await db.flush()
    return plan, execution


def build_execution_tasks(
    plan: CareerPlan, execution: CareerPlanExecution
) -> list[CareerPlanExecutionTask]:
    learning_path = plan.learning_path or {}
    stages = learning_path.get("stages") or []
    total_weeks = max(1, min(int(learning_path.get("total_weeks") or 12), 104))
    task_specs: list[dict] = []

    for stage_index, stage in enumerate(stages):
        if not isinstance(stage, dict):
            continue
        stage_name = str(stage.get("stage") or f"阶段 {stage_index + 1}")[:200]
        start_week, end_week = parse_stage_weeks(
            str(stage.get("duration") or ""), stage_index, len(stages), total_weeks
        )
        groups = (
            ("topics", "learning", "学习"),
            ("tasks", "learning", "完成"),
            ("practice_tasks", "practice", "实践"),
            ("deliverables", "deliverable", "产出"),
        )
        for field, task_type, prefix in groups:
            values = stage.get(field) or []
            for item_index, item in enumerate(values):
                title = str(item).strip()
                if title:
                    task_specs.append({
                        "key": f"stage:{stage_index}:{field}:{item_index}",
                        "title": f"{prefix}：{title}"[:255],
                        "description": "；".join(stage.get("goals") or [])[:1000] or None,
                        "task_type": task_type,
                        "stage": stage_name,
                        "start_week": start_week,
                        "end_week": end_week,
                    })

    action_plan = plan.action_plan or {}
    action_groups = (
        ("this_week", "practice", 1, 1, "本周行动"),
        ("this_month", "practice", 1, min(4, total_weeks), "本月行动"),
        ("portfolio_projects", "deliverable", 1, total_weeks, "项目作品"),
        ("resume_actions", "job_search", 1, min(4, total_weeks), "求职准备"),
    )
    for field, task_type, start_week, end_week, stage_name in action_groups:
        for item_index, item in enumerate(action_plan.get(field) or []):
            title = str(item).strip()
            if title:
                task_specs.append({
                    "key": f"action:{field}:{item_index}",
                    "title": title[:255],
                    "description": None,
                    "task_type": task_type,
                    "stage": stage_name,
                    "start_week": start_week,
                    "end_week": end_week,
                })

    for week_no in range(1, total_weeks + 1):
        for item_index, item in enumerate(action_plan.get("review_points") or []):
            title = str(item).strip()
            if title:
                task_specs.append({
                    "key": f"review:{week_no}:{item_index}",
                    "title": f"第 {week_no} 周复盘：{title}"[:255],
                    "description": None,
                    "task_type": "review",
                    "stage": "每周复盘",
                    "start_week": week_no,
                    "end_week": week_no,
                })

    if not task_specs:
        task_specs.append({
            "key": "fallback:review",
            "title": "复盘职业规划并记录本周行动",
            "description": None,
            "task_type": "review",
            "stage": "计划启动",
            "start_week": 1,
            "end_week": 1,
        })

    start_date = execution.start_date
    tasks: list[CareerPlanExecutionTask] = []
    for index, spec in enumerate(task_specs):
        span = max(1, spec["end_week"] - spec["start_week"] + 1)
        week_no = spec["start_week"] + (index % span)
        day_offset = (week_no - 1) * 7 + (index % 6)
        raw_key = f"{execution.career_plan_id}:{spec['key']}"
        tasks.append(CareerPlanExecutionTask(
            user_id=execution.user_id,
            execution_plan_id=execution.id,
            task_key=hashlib.sha256(raw_key.encode("utf-8")).hexdigest(),
            title=spec["title"],
            description=spec["description"],
            task_type=spec["task_type"],
            stage=spec["stage"],
            week_no=week_no,
            planned_date=start_date + timedelta(days=day_offset),
            is_required=spec["task_type"] != "review",
            status="pending",
        ))
    return tasks


def parse_stage_weeks(
    duration: str, stage_index: int, stage_count: int, total_weeks: int
) -> tuple[int, int]:
    match = re.search(r"(\d+)\s*(?:-|~|—|至)\s*(\d+)", duration)
    if match:
        start = max(1, min(int(match.group(1)), total_weeks))
        end = max(start, min(int(match.group(2)), total_weeks))
        return start, end
    count = max(1, stage_count)
    start = min(total_weeks, stage_index * total_weeks // count + 1)
    end = min(total_weeks, max(start, (stage_index + 1) * total_weeks // count))
    return start, end


async def get_current_execution_overview(db: AsyncSession, *, user_id: int) -> dict:
    execution = await get_current_execution(db, user_id)
    if execution is None:
        raise CareerPlanError("暂无正在执行的职业规划", 404)
    return await build_execution_overview(db, execution=execution, user_id=user_id)


async def check_in_execution_task(
    db: AsyncSession,
    *,
    user_id: int,
    task_id: int,
    request: CareerTaskCheckinRequest,
) -> dict:
    task = await get_owned_execution_task(db, task_id, user_id)
    if task is None:
        raise CareerPlanError("执行任务不存在", 404)
    execution = await get_execution_by_id(db, task.execution_plan_id, user_id)
    if execution is None or execution.status != "active":
        raise CareerPlanError("当前职业规划不在执行中", 409)

    if task.status == request.status:
        if request.note is not None:
            task.checkin_note = request.note
        await db.flush()
        return await build_execution_overview(db, execution=execution, user_id=user_id)

    now = utc_now_naive()
    task.status = request.status
    task.checkin_note = request.note
    task.checked_in_at = now if request.status in ("completed", "skipped") else None
    await create_checkin(db, CareerPlanCheckin(
        user_id=user_id,
        task_id=task.id,
        status=request.status,
        note=request.note,
        checked_in_at=now,
    ))
    return await build_execution_overview(db, execution=execution, user_id=user_id)


async def build_execution_overview(
    db: AsyncSession, *, execution: CareerPlanExecution, user_id: int
) -> dict:
    tasks = await get_execution_tasks(db, execution.id, user_id)
    today = today_in_china()
    elapsed_days = max(0, (today - execution.start_date).days)
    max_week = max((task.week_no for task in tasks), default=1)
    current_week = min(max_week, elapsed_days // 7 + 1)
    week_start = execution.start_date + timedelta(days=(current_week - 1) * 7)
    week_end = week_start + timedelta(days=6)
    today_tasks = [task for task in tasks if task.planned_date == today]
    week_tasks = [
        task for task in tasks
        if task.planned_date is not None and week_start <= task.planned_date <= week_end
    ]
    current_stage = next(
        (task.stage for task in week_tasks if task.status != "completed"),
        week_tasks[0].stage if week_tasks else "按计划稳步前进",
    )
    completed = sum(task.status == "completed" for task in tasks)
    total = len(tasks)
    current_streak, longest_streak = calculate_streaks(tasks, today)
    recent = await get_recent_checkins(db, execution.id, user_id)
    return {
        "id": execution.id,
        "career_plan_id": execution.career_plan_id,
        "status": execution.status,
        "start_date": execution.start_date,
        "end_date": execution.end_date,
        "current_week": current_week,
        "current_stage": current_stage,
        "total_tasks": total,
        "completed_tasks": completed,
        "progress_percent": round(completed * 100 / total) if total else 0,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "today_tasks": [serialize_execution_task(task) for task in today_tasks],
        "week_tasks": [serialize_execution_task(task) for task in week_tasks],
        "recent_checkins": [
            {
                "id": checkin.id,
                "task_id": checkin.task_id,
                "task_title": title,
                "status": checkin.status,
                "note": checkin.note,
                "checked_in_at": checkin.checked_in_at,
            }
            for checkin, title in recent
        ],
    }


def serialize_execution_task(task: CareerPlanExecutionTask) -> dict:
    return {
        "id": task.id,
        "execution_plan_id": task.execution_plan_id,
        "title": task.title,
        "description": task.description,
        "task_type": task.task_type,
        "stage": task.stage,
        "week_no": task.week_no,
        "planned_date": task.planned_date,
        "is_required": task.is_required,
        "status": task.status,
        "checkin_note": task.checkin_note,
        "checked_in_at": task.checked_in_at,
    }


def calculate_streaks(
    tasks: list[CareerPlanExecutionTask], today: date
) -> tuple[int, int]:
    completed_dates = sorted({
        task.checked_in_at.replace(tzinfo=timezone.utc).astimezone(CHINA_TZ).date()
        for task in tasks
        if task.status == "completed" and task.checked_in_at is not None
    })
    if not completed_dates:
        return 0, 0

    longest = 1
    run = 1
    for previous, current in zip(completed_dates, completed_dates[1:]):
        if current == previous + timedelta(days=1):
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    anchor = today if today in completed_dates else today - timedelta(days=1)
    current = 0
    completed_set = set(completed_dates)
    while anchor in completed_set:
        current += 1
        anchor -= timedelta(days=1)
    return current, longest


# Extended execution contract used by advance and stage-assessment endpoints.
async def ensure_stage_progress(
    db: AsyncSession, *, execution: CareerPlanExecution, user_id: int,
    tasks: list[CareerPlanExecutionTask] | None = None,
) -> list[CareerStageProgress]:
    from app.crud.career_assessment import get_stage_progresses

    stages = await get_stage_progresses(db, execution.id, user_id)
    if stages:
        return stages
    tasks = tasks if tasks is not None else await get_execution_tasks(db, execution.id, user_id)
    plan = await get_plan(db, execution.career_plan_id, user_id)
    names = [
        str(item.get("stage") or f"阶段 {index + 1}")[:200]
        for index, item in enumerate((plan.learning_path or {}).get("stages") or [])
        if isinstance(item, dict)
    ] if plan is not None else []
    if not names:
        for task in tasks:
            if task.stage not in names:
                names.append(task.stage)
    max_week = max((item.week_no for item in tasks), default=1)
    for index, name in enumerate(names, 1):
        db.add(CareerStageProgress(
            user_id=user_id, execution_plan_id=execution.id, stage=name,
            stage_order=index, status="in_progress" if index == 1 else "locked",
        ))
        stage_tasks = [
            item for item in tasks
            if item.stage == name or (
                item.stage not in names
                and min(len(names), max(1, (item.week_no - 1) * len(names) // max_week + 1)) == index
            )
        ]
        for order, task in enumerate(stage_tasks):
            task.stage_order = index
            task.task_order = order
            task.is_active = index == 1
    await db.flush()
    return await get_stage_progresses(db, execution.id, user_id)


async def _active_assessment_id(
    db: AsyncSession, execution_id: int, stage_order: int
) -> int | None:
    from app.models.career_plan import CareerStageAssessment
    result = await db.execute(select(CareerStageAssessment.id).where(
        CareerStageAssessment.execution_plan_id == execution_id,
        CareerStageAssessment.stage_order == stage_order,
        CareerStageAssessment.status.in_(("generating", "ready", "submitted", "evaluating")),
    ).order_by(CareerStageAssessment.created_at.desc()).limit(1))
    return result.scalar_one_or_none()


async def build_execution_overview(
    db: AsyncSession, *, execution: CareerPlanExecution, user_id: int
) -> dict:
    tasks = await get_execution_tasks(db, execution.id, user_id)
    stages = await ensure_stage_progress(db, execution=execution, user_id=user_id, tasks=tasks)
    today = today_in_china()
    elapsed_days = max(0, (today - execution.start_date).days)
    max_week = max((task.week_no for task in tasks), default=1)
    current_week = min(max_week, elapsed_days // 7 + 1)
    week_start = execution.start_date + timedelta(days=(current_week - 1) * 7)
    week_end = week_start + timedelta(days=6)
    visible = [task for task in tasks if task.is_active]
    today_tasks = [task for task in visible if task.planned_date == today]
    week_tasks = [task for task in visible if task.planned_date and week_start <= task.planned_date <= week_end]
    stage_row = next((item for item in stages if item.status not in ("locked", "passed")), stages[-1] if stages else None)
    stage_tasks = [task for task in tasks if stage_row and task.stage_order == stage_row.stage_order]
    required_stage = [task for task in stage_tasks if task.is_required]
    stage_done = sum(task.status == "completed" for task in required_stage)
    assessment_ready = bool(required_stage) and stage_done == len(required_stage)
    if stage_row and assessment_ready and stage_row.status in ("in_progress", "needs_improvement"):
        stage_row.status = "ready_for_assessment"
    required_today = [task for task in today_tasks if task.is_required]
    today_completed = bool(required_today) and all(task.status == "completed" for task in required_today)
    future = [task for task in stage_tasks if task.is_active and task.status == "pending" and task.planned_date and task.planned_date > today]
    ahead_today = [task for task in tasks if task.is_advanced and task.advanced_at and task.advanced_at.replace(tzinfo=timezone.utc).astimezone(CHINA_TZ).date() == today]
    completed = sum(task.status == "completed" for task in tasks)
    recent = await get_recent_checkins(db, execution.id, user_id)
    current_streak, longest_streak = calculate_streaks(tasks, today)
    return {
        "id": execution.id, "career_plan_id": execution.career_plan_id,
        "status": execution.status, "start_date": execution.start_date, "end_date": execution.end_date,
        "current_week": current_week, "current_stage": stage_row.stage if stage_row else "按计划稳步前进",
        "total_tasks": len(tasks), "completed_tasks": completed,
        "progress_percent": round(completed * 100 / len(tasks)) if tasks else 0,
        "current_streak": current_streak, "longest_streak": longest_streak,
        "today_tasks": [serialize_execution_task(item) for item in today_tasks],
        "week_tasks": [serialize_execution_task(item) for item in week_tasks],
        "recent_checkins": [{"id": item.id, "task_id": item.task_id, "task_title": title, "status": item.status, "note": item.note, "checked_in_at": item.checked_in_at} for item, title in recent],
        "today_completed": today_completed,
        "can_advance": today_completed and bool(future) and len(ahead_today) < 3,
        "next_task_available": bool(future), "ahead_task_count": len(ahead_today),
        "ahead_days": max(((item.original_planned_date - today).days for item in ahead_today if item.original_planned_date), default=0),
        "stage_progress": round(stage_done * 100 / len(required_stage)) if required_stage else 0,
        "assessment_ready": assessment_ready,
        "current_stage_status": stage_row.status if stage_row else "in_progress",
        "active_assessment_id": await _active_assessment_id(db, execution.id, stage_row.stage_order if stage_row else 0),
    }


def serialize_execution_task(task: CareerPlanExecutionTask) -> dict:
    return {
        "id": task.id, "execution_plan_id": task.execution_plan_id, "title": task.title,
        "description": task.description, "task_type": task.task_type, "stage": task.stage,
        "week_no": task.week_no, "planned_date": task.planned_date, "is_required": task.is_required,
        "status": task.status, "checkin_note": task.checkin_note, "checked_in_at": task.checked_in_at,
        "is_advanced": task.is_advanced, "original_planned_date": task.original_planned_date,
        "advanced_at": task.advanced_at,
    }


async def advance_execution_task(
    db: AsyncSession, *, user_id: int, execution_plan_id: int
) -> dict:
    await db.execute(select(User.id).where(User.id == user_id).with_for_update())
    execution = await get_execution_by_id(db, execution_plan_id, user_id)
    if execution is None:
        raise CareerPlanError("执行计划不存在", 404)
    if execution.status != "active":
        raise CareerPlanError("当前职业规划不在执行中", 409)
    overview = await build_execution_overview(db, execution=execution, user_id=user_id)
    if not overview["today_completed"]:
        raise CareerPlanError("完成今日全部必做任务后才能提前推进", 409)
    if overview["ahead_task_count"] >= 3:
        raise CareerPlanError("每日最多提前推进 3 个任务", 409)
    tasks = await get_execution_tasks(db, execution.id, user_id)
    today = today_in_china()
    next_task = next((item for item in tasks if item.is_active and item.status == "pending" and item.planned_date and item.planned_date > today), None)
    if next_task is None:
        raise CareerPlanError("暂无可提前推进的任务", 409)
    next_task.original_planned_date = next_task.original_planned_date or next_task.planned_date
    next_task.planned_date = today
    next_task.is_advanced = True
    next_task.advanced_at = utc_now_naive()
    await db.flush()
    return {"overview": await build_execution_overview(db, execution=execution, user_id=user_id), "advanced_task": serialize_execution_task(next_task)}
