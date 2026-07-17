from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import BrowserContext, async_playwright
from sqlalchemy import select

import app.models  # noqa: F401 - load all ORM tables for FK resolution
from app.core.config import settings
from app.core.database import async_session, engine
from app.models.job import JobPlatformLoginSession
from app.services.platform_session_service import LOGIN_URLS, encrypt_storage_state_file
from app.services.operational_alert_service import emit_operational_alert
from app.services.recommendation_start_service import (
    RecommendationStartError,
    ensure_recommendation_task,
    mark_login_pending_task_need_login,
)


POLL_SECONDS = 2
SESSION_WAIT_SECONDS = 10


def configure_event_loop() -> None:
    if sys.platform != "win32":
        return
    policy_factory = getattr(asyncio, "WindowsProactorEventLoopPolicy", None)
    if policy_factory is not None:
        asyncio.set_event_loop_policy(policy_factory())


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


async def wait_for_session(session_id: str) -> JobPlatformLoginSession | None:
    deadline = asyncio.get_running_loop().time() + SESSION_WAIT_SECONDS
    while True:
        async with async_session() as db:
            result = await db.execute(
                select(JobPlatformLoginSession).where(JobPlatformLoginSession.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session is not None:
                return session
        if asyncio.get_running_loop().time() >= deadline:
            return None
        await asyncio.sleep(0.5)


async def update_login_session(session_id: str, **values) -> None:
    async with async_session() as db:
        result = await db.execute(
            select(JobPlatformLoginSession).where(JobPlatformLoginSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            return
        for key, value in values.items():
            setattr(session, key, value)
        if values.get("status") in ("failed", "expired"):
            await mark_login_pending_task_need_login(
                db,
                user_id=session.user_id,
                login_session_id=session.id,
                message=values.get("error_message") or "登录未完成，请重新发起登录",
            )
        await db.commit()


async def auto_start_recommendation(session_id: str) -> None:
    async with async_session() as db:
        result = await db.execute(
            select(JobPlatformLoginSession).where(JobPlatformLoginSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session is None or session.status != "logged_in":
            return
        try:
            await ensure_recommendation_task(
                db,
                user_id=session.user_id,
                resume_id=session.resume_id,
                resume_source=session.resume_source,
                resume_optimization_id=session.resume_optimization_id,
                source=session.source,
                login_session_id=session.id,
                limit=20,
            )
        except RecommendationStartError as exc:
            session.error_message = f"登录成功，但自动推荐启动失败：{exc.message}"
        await db.commit()


async def is_logged_in(context: BrowserContext) -> bool:
    pages = [page for page in context.pages if not page.is_closed()]
    if not pages:
        return False
    url = pages[-1].url.lower()
    if not all(marker not in url for marker in ("login", "passport", "verify", "antibot")):
        return False
    cookies = await context.cookies()
    auth_names = {"id58", "PPU", "www58com", "58cooper", "passportAccount"}
    return any(
        cookie.get("name") in auth_names and "58.com" in (cookie.get("domain") or "")
        for cookie in cookies
    )


async def session_still_waiting(session_id: str) -> bool:
    async with async_session() as db:
        status = (await db.execute(
            select(JobPlatformLoginSession.status).where(JobPlatformLoginSession.id == session_id)
        )).scalar_one_or_none()
        return status == "waiting_login"


async def run_login(session_id: str) -> None:
    session = await wait_for_session(session_id)
    if session is None:
        await engine.dispose()
        return
    if session.source not in LOGIN_URLS:
        await update_login_session(
            session_id,
            status="failed",
            error_message="当前不支持该招聘平台",
        )
        await engine.dispose()
        return

    expires_at = normalize_datetime(session.expires_at)
    if expires_at <= utc_now_naive():
        await update_login_session(session_id, status="expired")
        await engine.dispose()
        return

    playwright = None
    browser = None
    context = None
    try:
        playwright = await async_playwright().start()
        if settings.PLAYWRIGHT_CDP_ENDPOINT.strip():
            browser = await playwright.chromium.connect_over_cdp(
                settings.PLAYWRIGHT_CDP_ENDPOINT.strip()
            )
        else:
            browser = await playwright.chromium.launch(headless=settings.PLAYWRIGHT_HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(LOGIN_URLS[session.source], wait_until="domcontentloaded")
        await prefer_qr_login(page)

        while utc_now_naive() < expires_at:
            if not await session_still_waiting(session_id):
                return
            pages = [item for item in context.pages if not item.is_closed()]
            if not pages:
                await update_login_session(
                    session_id,
                    status="failed",
                    error_message="登录浏览器窗口已关闭，请重新登录",
                )
                emit_operational_alert(
                    category="platform_login_browser_closed",
                    message="登录浏览器窗口已关闭，请重新登录",
                    severity="warning",
                    context={"session_id": session_id, "user_id": session.user_id},
                )
                return
            if await is_logged_in(context):
                state_dir = Path(settings.PLATFORM_STATE_DIR).resolve() / str(session.user_id)
                state_dir.mkdir(parents=True, exist_ok=True)
                plain_state_path = state_dir / f"{session.source}.json.tmp"
                state_path = state_dir / f"{session.source}.enc"
                await context.storage_state(path=str(plain_state_path))
                encrypt_storage_state_file(plain_state_path, state_path)
                await update_login_session(
                    session_id,
                    status="logged_in",
                    storage_state_ref=str(state_path),
                    manual_login_verified=True,
                    manual_login_verified_at=utc_now_naive(),
                    error_message=None,
                )
                await auto_start_recommendation(session_id)
                return
            await asyncio.sleep(POLL_SECONDS)

        await update_login_session(
            session_id,
            status="expired",
            error_message="登录超时，请重新发起登录",
        )
        emit_operational_alert(
            category="platform_login_timeout",
            message="登录超时，请重新发起登录",
            severity="warning",
            context={"session_id": session_id, "user_id": session.user_id},
        )
    except Exception as exc:
        safe_error = f"无法启动或完成登录浏览器: {exc}"[:1000]
        await update_login_session(
            session_id,
            status="failed",
            error_message=safe_error,
        )
        emit_operational_alert(
            category="platform_login_worker_failed",
            message=safe_error,
            context={"session_id": session_id, "user_id": session.user_id},
        )
    finally:
        if context is not None:
            await context.close()
        if browser is not None:
            await browser.close()
        if playwright is not None:
            await playwright.stop()
        await engine.dispose()


async def prefer_qr_login(page) -> None:
    """Best-effort switch to QR login when the platform exposes that tab."""
    for text in ("扫码登录", "二维码登录", "扫码"):
        try:
            locator = page.get_by_text(text, exact=False).first
            if await locator.count():
                await locator.click(timeout=1500)
                return
        except Exception:
            continue


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python -m app.workers.platform_login_worker <session_id>")
        return 2
    configure_event_loop()
    asyncio.run(run_login(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
