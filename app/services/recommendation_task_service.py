"""岗位推荐任务编排服务。"""
import traceback
import re
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.models  # noqa: F401 - load all ORM tables for FK resolution
from app.core.database import async_session
from app.crawlers.job_58_playwright import Job58PlaywrightCrawler, LoginExpiredError
from app.crud.job import bulk_save_jobs, get_job_by_source
from app.crud.job_recommendation import create_recommend_result, update_task
from app.models.job import JobPlatformLoginSession, JobRecommendResult, JobRecommendTask
from app.models.resume import Resume
from app.services.skills_service import score_skills


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


async def run_recommendation_task(task_id: str) -> None:
    """后台执行一次岗位采集、入库和规则匹配。"""
    async with async_session() as db:
        task = (await db.execute(
            select(JobRecommendTask).where(JobRecommendTask.id == task_id)
        )).scalar_one_or_none()
        if task is None:
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

        resume = (await db.execute(
            select(Resume).where(Resume.id == task.resume_id, Resume.user_id == task.user_id)
        )).scalar_one_or_none()
        target_city = infer_resume_city(
            resume.structured_data if resume else None,
            resume.extracted_text if resume else None,
        )

        await update_task(
            db, task_id, status="crawling", progress=10,
            started_at=datetime.now(timezone.utc),
        )
        await db.commit()

    try:
        crawler = Job58PlaywrightCrawler()
        jobs_data = await crawler.crawl(
            str(storage_state), task.extracted_skills or [], task.requested_limit, target_city,
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
    except Exception as exc:
        traceback.print_exc()
        detail = f"{type(exc).__name__}: {exc}"
        async with async_session() as db:
            await update_task(
                db, task_id, status="failed", progress=100,
                error_message=f"岗位采集失败：{detail[:300]}", finished_at=datetime.now(timezone.utc),
            )
            await db.commit()
        return

    async with async_session() as db:
        task = (await db.execute(
            select(JobRecommendTask).where(JobRecommendTask.id == task_id)
        )).scalar_one()
        await update_task(db, task_id, status="matching", progress=80, total_found=len(jobs_data))
        saved = await bulk_save_jobs(db, jobs_data)
        await update_task(db, task_id, progress=90, total_saved=saved)

        matched_count = 0
        for raw in jobs_data:
            job = await get_job_by_source(db, raw["source"], raw["source_id"])
            if job is None:
                continue
            score, matched_skills, reasons = score_skills(task.extracted_skills or [], job.skills or [])
            if not matched_skills:
                score, matched_skills, reasons = score_keyword_text(
                    task.extracted_skills or [],
                    " ".join([
                        job.title or "",
                        job.company or "",
                        job.description or "",
                    ]),
                )
            if not matched_skills:
                score = 1
                reasons = ["采集自当前简历关键词搜索结果"]
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

        await update_task(
            db, task_id, status="success", progress=100,
            total_matched=matched_count, finished_at=datetime.now(timezone.utc),
        )
        await db.commit()


def infer_resume_city(structured_data: dict | None, extracted_text: str | None) -> str:
    text = extracted_text or ""
    location = ((structured_data or {}).get("basic_info") or {}).get("location")
    candidates = [location or ""]
    patterns = [
        r"期望城市[：:]\s*([\u4e00-\u9fff]{2,4})",
        r"城市[：:]\s*([\u4e00-\u9fff]{2,4})",
        r"现居[：:]\s*([\u4e00-\u9fff]{2,4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            candidates.append(match.group(1))
    for value in candidates:
        city = value.replace("市", "").strip()
        if city in Job58PlaywrightCrawler.CITY_CODES:
            return city
    return "北京"


def score_keyword_text(keywords: list[str], text: str) -> tuple[int, list[str], list[str]]:
    text_lower = text.lower()
    matched = []
    for keyword in keywords:
        if keyword and keyword.lower() in text_lower:
            matched.append(keyword)
    if not matched:
        return 0, [], []
    matched = list(dict.fromkeys(matched))
    score = min(100, 30 + len(matched) * 20)
    return score, matched, [f"搜索关键词匹配: {item}" for item in matched[:5]]
