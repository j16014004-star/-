"""岗位推荐任务编排服务。"""
import traceback
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

import app.models  # noqa: F401 - load all ORM tables for FK resolution
from app.ai.knowledge import JobRecommendationKnowledgeRetriever, role_knowledge_filters
from app.core.database import async_session
from app.crawlers.job_58_playwright import (
    Job58PlaywrightCrawler,
    JobPageParseError,
    LoginExpiredError,
    NetworkAccessDeniedError,
)
from app.crud.job import bulk_save_jobs, get_job_by_source
from app.crud.job_recommendation import create_recommend_result, update_task
from app.models.job import Job, JobPlatformLoginSession, JobRecommendResult, JobRecommendTask
from app.services.job_recommendation_rules import (
    expand_search_keywords_from_knowledge,
    score_job_match,
)


async def update_login_session_status(
    session_id: str | None,
    status: str,
    error_message: str | None = None,
    clear_state: bool = False,
) -> None:
    if not session_id:
        return
    async with async_session() as db:
        result = await db.execute(
            select(JobPlatformLoginSession).where(JobPlatformLoginSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            return
        if clear_state and session.storage_state_ref:
            state_path = Path(session.storage_state_ref)
            if state_path.is_file():
                try:
                    state_path.unlink()
                except OSError:
                    pass
            session.storage_state_ref = None
        session.status = status
        session.error_message = error_message
        await db.commit()


def advance_missing_counts(
    tracked_misses: dict[str, int],
    seen_job_ids: set[int],
) -> tuple[dict[str, int], list[int]]:
    """Advance one successful search cycle without penalizing a single miss."""
    current_ids = {int(job_id) for job_id in seen_job_ids}
    next_tracked: dict[str, int] = {}
    deactivated_ids: list[int] = []
    for raw_job_id, previous_misses in tracked_misses.items():
        job_id = int(raw_job_id)
        if job_id in current_ids:
            next_tracked[raw_job_id] = 0
            continue
        misses = max(0, int(previous_misses)) + 1
        next_tracked[raw_job_id] = misses
        if misses >= 2:
            deactivated_ids.append(job_id)
    for job_id in current_ids:
        next_tracked[str(job_id)] = 0
    return next_tracked, deactivated_ids


async def reconcile_job_freshness(
    db: AsyncSession,
    *,
    task: JobRecommendTask,
    seen_job_ids: set[int],
    diagnostics: dict | None,
) -> dict:
    """Carry per-search miss counts across tasks and deactivate only after two misses."""
    previous = (await db.execute(
        select(JobRecommendTask)
        .where(
            JobRecommendTask.id != task.id,
            JobRecommendTask.user_id == task.user_id,
            JobRecommendTask.source == task.source,
            JobRecommendTask.target_role == task.target_role,
            JobRecommendTask.target_city == task.target_city,
            JobRecommendTask.status.in_(("success", "no_results")),
            JobRecommendTask.created_at < task.created_at,
        )
        .order_by(JobRecommendTask.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()

    tracked: dict[str, int] = {}
    if previous:
        previous_freshness = (previous.crawl_diagnostics or {}).get("freshness") or {}
        raw_tracked = previous_freshness.get("tracked_misses") or {}
        tracked = {
            str(job_id): max(0, int(misses))
            for job_id, misses in raw_tracked.items()
            if str(job_id).isdigit()
        }
        if not tracked:
            previous_ids = list((await db.scalars(
                select(JobRecommendResult.job_id).where(
                    JobRecommendResult.task_id == previous.id
                )
            )).all())
            if not previous_ids:
                seed_task_id = await db.scalar(
                    select(JobRecommendResult.task_id)
                    .join(
                        JobRecommendTask,
                        JobRecommendTask.id == JobRecommendResult.task_id,
                    )
                    .where(
                        JobRecommendTask.id != task.id,
                        JobRecommendTask.user_id == task.user_id,
                        JobRecommendTask.source == task.source,
                        JobRecommendTask.target_role == task.target_role,
                        JobRecommendTask.target_city == task.target_city,
                        JobRecommendTask.created_at < task.created_at,
                    )
                    .order_by(JobRecommendTask.created_at.desc())
                    .limit(1)
                )
                if seed_task_id:
                    previous_ids = list((await db.scalars(
                        select(JobRecommendResult.job_id).where(
                            JobRecommendResult.task_id == seed_task_id
                        )
                    )).all())
            tracked = {str(job_id): 0 for job_id in previous_ids}

    current_ids = {int(job_id) for job_id in seen_job_ids}
    next_tracked, deactivated_ids = advance_missing_counts(tracked, current_ids)

    if current_ids:
        await db.execute(
            update(Job).where(Job.id.in_(current_ids)).values(is_active=True)
        )
    if deactivated_ids:
        await db.execute(
            update(Job).where(Job.id.in_(deactivated_ids)).values(is_active=False)
        )

    result = dict(diagnostics or {})
    result["freshness"] = {
        "tracked_misses": next_tracked,
        "deactivated_job_ids": deactivated_ids,
        "policy": "two_consecutive_misses",
    }
    return result


async def run_recommendation_task(task_id: str) -> None:
    """后台执行一次岗位采集、入库和规则匹配。"""
    async with async_session() as db:
        task = (await db.execute(
            select(JobRecommendTask).where(JobRecommendTask.id == task_id)
        )).scalar_one_or_none()
        if task is None:
            return
        if task.status not in ("pending", "crawling"):
            return

        if task.source != "58":
            await update_task(
                db, task_id, status="failed", progress=100,
                error_message="当前不支持该招聘平台", finished_at=datetime.now(timezone.utc),
            )
            await db.commit()
            return

        login_session = None
        if task.login_session_id:
            login_session = (await db.execute(
                select(JobPlatformLoginSession).where(JobPlatformLoginSession.id == task.login_session_id)
            )).scalar_one_or_none()
        if not login_session or not login_session.storage_state_ref:
            await update_task(
                db, task_id, status="need_login", progress=100,
                error_message="登录态不存在或已失效", finished_at=datetime.now(timezone.utc),
            )
            await db.commit()
            return

        storage_state = Path(login_session.storage_state_ref)
        if not storage_state.is_file():
            await update_task(
                db, task_id, status="need_login", progress=100,
                error_message="登录态不存在或已失效", finished_at=datetime.now(timezone.utc),
            )
            await db.commit()
            return

        target_city = task.target_city or "北京"

        await update_task(
            db, task_id, status="crawling", progress=10,
            started_at=datetime.now(timezone.utc),
        )
        await db.commit()

    retriever = JobRecommendationKnowledgeRetriever()
    try:
        retrieval_query = " ".join(
            [
                task.target_role or "",
                task.target_city or "",
                " ".join(task.extracted_skills or []),
            ]
        )
        knowledge_chunks = await retriever.retrieve(
            retrieval_query,
            top_k=3,
            filters=role_knowledge_filters(retrieval_query),
        )
    except Exception as exc:
        knowledge_chunks = []
        retriever.last_source = "unavailable"
        retriever.last_error = f"{type(exc).__name__}: {exc}"[:500]
        retriever.last_results = []
    crawl_keywords = expand_search_keywords_from_knowledge(
        task.target_role or "",
        list(task.search_keywords or []),
        knowledge_chunks,
    )
    knowledge_context = "\n".join(chunk.content for chunk in knowledge_chunks)

    try:
        crawler = Job58PlaywrightCrawler()
        jobs_data = await crawler.crawl(
            str(storage_state), crawl_keywords, task.requested_limit, target_city,
        )
    except LoginExpiredError:
        await update_login_session_status(
            task.login_session_id,
            "expired",
            "平台要求重新登录或人工验证",
            clear_state=True,
        )
        async with async_session() as db:
            await update_task(
                db, task_id, status="need_login", progress=100,
                error_message="平台要求重新登录或人工验证", finished_at=datetime.now(timezone.utc),
            )
            await db.commit()
        return
    except JobPageParseError as exc:
        async with async_session() as db:
            await update_task(
                db,
                task_id,
                status="failed",
                progress=100,
                failure_code="parse_failed",
                error_message=str(exc)[:500],
                crawl_diagnostics=exc.diagnostics,
                finished_at=datetime.now(timezone.utc),
            )
            await db.commit()
        return
    except NetworkAccessDeniedError as exc:
        async with async_session() as db:
            await update_task(
                db,
                task_id,
                status="failed",
                progress=100,
                failure_code="network_access_denied",
                error_message=str(exc)[:500],
                finished_at=datetime.now(timezone.utc),
            )
            await db.commit()
        return
    except Exception as exc:
        traceback.print_exc()
        detail = f"{type(exc).__name__}: {exc}"
        async with async_session() as db:
            await update_task(
                db, task_id, status="failed", progress=100,
                failure_code="crawl_failed",
                error_message=f"岗位采集失败：{detail[:300]}",
                finished_at=datetime.now(timezone.utc),
            )
            await db.commit()
        return

    async with async_session() as db:
        task = (await db.execute(
            select(JobRecommendTask).where(JobRecommendTask.id == task_id)
        )).scalar_one()
        if task.failure_code == "superseded_by_new_resume" or task.status == "failed":
            return
        diagnostics = crawler.last_diagnostics
        diagnostics["knowledge_retrieval"] = {
            "source": retriever.last_source,
            "error": retriever.last_error,
            "chunks": retriever.last_results,
            "search_keywords": crawl_keywords,
        }
        if not jobs_data:
            diagnostics = await reconcile_job_freshness(
                db, task=task, seen_job_ids=set(), diagnostics=diagnostics,
            )
            await update_task(
                db,
                task_id,
                status="no_results",
                progress=100,
                total_found=0,
                total_saved=0,
                total_matched=0,
                failure_code="no_exact_results",
                error_message="当前目标岗位和城市暂无精准岗位，请调整条件后重试",
                crawl_diagnostics=diagnostics,
                finished_at=datetime.now(timezone.utc),
            )
            await db.commit()
            return

        await update_task(
            db,
            task_id,
            status="matching",
            progress=80,
            total_found=len(jobs_data),
            crawl_diagnostics=diagnostics,
        )
        saved = await bulk_save_jobs(db, jobs_data)
        await update_task(db, task_id, progress=90, total_saved=saved)

        matched_count = 0
        seen_job_ids: set[int] = set()
        for raw in jobs_data:
            job = await get_job_by_source(db, raw["source"], raw["source_id"])
            if job is None:
                continue
            seen_job_ids.add(job.id)
            score, matched_skills, reasons, relevant = score_job_match(
                target_role=task.target_role or "通用岗位",
                target_city=task.target_city or "北京",
                resume_skills=task.extracted_skills or [],
                job_title=job.title or "",
                job_city=job.city,
                job_skills=job.skills or [],
                job_description=job.description,
                knowledge_context=knowledge_context,
            )
            if not relevant:
                continue
            await create_recommend_result(
                db,
                JobRecommendResult(
                    task_id=task.id,
                    user_id=task.user_id,
                    resume_id=task.resume_id,
                    job_id=job.id,
                    match_score=score,
                    matched_skills=matched_skills,
                    matched_skill_count=len(matched_skills),
                    match_reasons=reasons,
                ),
            )
            matched_count += 1

        diagnostics = await reconcile_job_freshness(
            db, task=task, seen_job_ids=seen_job_ids, diagnostics=diagnostics,
        )
        terminal_status = "success" if matched_count else "no_results"
        await update_task(
            db,
            task_id,
            status=terminal_status,
            progress=100,
            total_matched=matched_count,
            failure_code=None if matched_count else "no_matching_jobs",
            error_message=None if matched_count else "已抓取岗位，但没有符合目标岗位方向的结果",
            crawl_diagnostics=diagnostics,
            finished_at=datetime.now(timezone.utc),
        )
        await db.commit()
