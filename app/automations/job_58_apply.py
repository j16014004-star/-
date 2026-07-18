"""Conservative 58.com application adapter used only after user confirmation."""
from __future__ import annotations

import re
import hashlib
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

from app.core.config import settings
from app.services.platform_session_service import load_storage_state


class PlatformLoginExpired(RuntimeError):
    pass


class PlatformActionError(RuntimeError):
    pass


class PlatformJobClosed(PlatformActionError):
    pass


class PlatformJobMismatch(PlatformActionError):
    pass


class PlatformNetworkDenied(PlatformActionError):
    pass


LOGIN_MARKERS = ("login", "passport", "verify", "antibot", "验证码", "请登录", "重新登录")
SUCCESS_MARKERS = ("投递成功", "申请成功", "已申请", "已投递", "简历已投递")
ALREADY_APPLIED_MARKERS = ("已申请", "已投递", "简历已投递")
CLOSED_MARKERS = (
    "职位已关闭", "岗位已关闭", "职位已下架", "岗位已下架", "招聘已结束",
    "职位不存在", "岗位不存在", "信息已删除", "页面不存在",
)


def normalize_job_title(value: str) -> str:
    normalized = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", (value or "").lower())
    for token in ("招聘", "急聘", "高薪", "诚聘"):
        normalized = normalized.replace(token, "")
    return normalized


def job_titles_match(expected_title: str, page_text: str) -> bool:
    expected = normalize_job_title(expected_title)
    actual = normalize_job_title(page_text)
    if len(expected) < 2 or len(actual) < 2:
        return False
    if expected in actual:
        return True
    # 58列表标题和详情标题经常带不同前后缀；相似度只作为source_id缺失时的降级校验。
    sample = actual[: max(len(expected) * 3, 80)]
    return SequenceMatcher(None, expected, sample).ratio() >= 0.62


def page_matches_job(
    *, expected_source_id: str | None, expected_title: str,
    current_url: str, page_html: str, page_text: str,
) -> bool:
    source_id = (expected_source_id or "").strip()
    if source_id:
        return source_id in current_url or source_id in page_html
    return job_titles_match(expected_title, page_text)


def classify_job_page(page_text: str) -> str:
    if any(marker in page_text for marker in CLOSED_MARKERS):
        return "closed"
    if any(marker in page_text for marker in ALREADY_APPLIED_MARKERS):
        return "already_applied"
    return "available"


def is_direct_58_job_url(url: str | None) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":", 1)[0]
    path = parsed.path.lower().rstrip("/")
    if parsed.scheme not in ("http", "https") or not (
        host == "58.com" or host.endswith(".58.com")
    ):
        return False
    if host == "legoclick.58.com" and path.startswith("/jump"):
        return True
    generic_paths = ("", "/job", "/quanzhizhaopin", "/job.shtml")
    return path not in generic_paths and "quanzhizhaopin" not in path


def is_58_webim_url(url: str | None) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and parsed.netloc.lower() == "webim.58.com"


def platform_error_message(exc: BaseException) -> str:
    detail = str(exc).strip()
    return detail or f"{type(exc).__name__}: 未提供详细错误"


def is_network_access_denied(exc: BaseException) -> bool:
    detail = platform_error_message(exc).lower()
    return any(marker in detail for marker in (
        "err_network_access_denied",
        "network access denied",
        "access is denied",
        "eacces",
        "eperm",
    ))


async def goto_58_page(page, url: str, *, timeout: int = 30000) -> None:
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
    except PlaywrightError as exc:
        if is_network_access_denied(exc):
            raise PlatformNetworkDenied(
                "运行环境无法访问58同城（ERR_NETWORK_ACCESS_DENIED），"
                "请放行Python/Chromium访问*.58.com后重试"
            ) from exc
        raise PlatformActionError(
            f"58页面访问失败：{platform_error_message(exc)[:400]}"
        ) from exc


async def create_58_browser_context(playwright, storage_state: str):
    endpoint = settings.PLAYWRIGHT_CDP_ENDPOINT.strip()
    browser = None
    try:
        browser = (
            await playwright.chromium.connect_over_cdp(endpoint)
            if endpoint
            else await playwright.chromium.launch(
                headless=settings.PLAYWRIGHT_CRAWL_HEADLESS
            )
        )
        context = await browser.new_context(
            storage_state=load_storage_state(storage_state)
        )
        return browser, context
    except PlaywrightError as exc:
        if browser is not None and not endpoint:
            await browser.close()
        if is_network_access_denied(exc):
            raise PlatformNetworkDenied(
                "运行环境无法访问远程浏览器或58同城，请检查网络放行规则"
            ) from exc
        target = "远程浏览器" if endpoint else "本地Chromium"
        raise PlatformActionError(
            f"无法启动{target}：{platform_error_message(exc)[:400]}"
        ) from exc
    except BaseException:
        if browser is not None and not endpoint:
            await browser.close()
        raise


async def close_58_browser_context(browser, context) -> None:
    """Close only resources owned by this task; never terminate shared CDP Chromium."""
    try:
        if context is not None:
            await context.close()
    finally:
        if browser is not None and not settings.PLAYWRIGHT_CDP_ENDPOINT.strip():
            await browser.close()


def infer_message_sender_from_class(class_name: str) -> str | None:
    value = class_name.lower()
    if any(marker in value for marker in ("receive", "received", "left", "other", "incoming")):
        return "hr"
    if any(marker in value for marker in ("send", "sent", "right", "self", "outgoing")):
        return "user"
    return None


async def first_visible_text(page, label: str, *, exact: bool = False):
    candidates = page.get_by_text(label, exact=exact)
    for index in range(min(await candidates.count(), 30)):
        candidate = candidates.nth(index)
        try:
            if await candidate.is_visible():
                return candidate
        except Exception:
            continue
    return None


async def first_visible_selector(page, selector: str):
    candidates = page.locator(selector)
    for index in range(min(await candidates.count(), 30)):
        candidate = candidates.nth(index)
        try:
            if await candidate.is_visible():
                return candidate
        except Exception:
            continue
    return None


async def upload_selected_resume(page, resume_file_path: str) -> str:
    """Select the exact local PDF without silently falling back to a platform resume."""
    file_path = Path(resume_file_path)
    if not file_path.is_file() or file_path.suffix.lower() != ".pdf":
        raise PlatformActionError("待投递简历PDF不存在，已停止投递")

    inputs = page.locator("input[type='file']")
    for index in range(min(await inputs.count(), 20)):
        candidate = inputs.nth(index)
        try:
            await candidate.set_input_files(str(file_path))
            selected_name = await candidate.evaluate(
                "(element) => element.files && element.files[0] ? element.files[0].name : ''"
            )
            if selected_name == file_path.name:
                await page.wait_for_timeout(800)
                return "direct_file_input"
        except Exception:
            continue

    for label in ("上传简历", "上传附件简历", "更换简历", "选择本地简历"):
        trigger = await first_visible_text(page, label)
        if trigger is None:
            continue
        try:
            async with page.expect_file_chooser(timeout=2500) as chooser_info:
                await trigger.click(timeout=2500)
            chooser = await chooser_info.value
            await chooser.set_files(str(file_path))
            await page.wait_for_timeout(800)
            return f"file_chooser:{label}"
        except PlaywrightTimeoutError:
            # Some platform versions reveal a hidden file input after the click.
            revealed = page.locator("input[type='file']")
            for index in range(min(await revealed.count(), 20)):
                candidate = revealed.nth(index)
                try:
                    await candidate.set_input_files(str(file_path))
                    selected_name = await candidate.evaluate(
                        "(element) => element.files && element.files[0] ? element.files[0].name : ''"
                    )
                    if selected_name == file_path.name:
                        await page.wait_for_timeout(800)
                        return f"revealed_file_input:{label}"
                except Exception:
                    continue
        except Exception:
            continue

    body = (await page.locator("body").inner_text(timeout=10000))[:50000]
    if any(marker in body for marker in ("在线简历", "平台简历", "默认简历", "选择简历")):
        raise PlatformActionError(
            "58当前页面仅发现平台已有/默认简历，无法验证与用户所选版本一致，已停止投递"
        )
    raise PlatformActionError("58当前岗位未提供可核验的简历上传入口，已停止投递")


async def click_with_58_safety_popup(page, locator) -> None:
    """Acknowledge 58's anti-fraud notice, then repeat the intended click."""
    try:
        await locator.click(timeout=1800)
        return
    except Exception as original_error:
        popup = await first_visible_selector(page, ".danger-pop-main")
        if popup is None:
            raise original_error
        acknowledge = await first_visible_selector(
            page, ".danger-pop-btn, .danger-pop-close"
        )
        if acknowledge is not None:
            await acknowledge.click(timeout=3000)
        else:
            await page.wait_for_timeout(5500)
        await locator.click(timeout=3000)


async def open_58_webim_scope(page, entry):
    """Load WebIM, then repeat the job-bound click so 58 activates that conversation."""
    await click_with_58_safety_popup(page, entry)
    webim = None
    for _ in range(12):
        webim = next(
            (frame for frame in page.frames if "webim.58.com" in frame.url),
            None,
        )
        if webim is not None:
            break
        await page.wait_for_timeout(500)
    if webim is None:
        raise PlatformActionError("58微聊窗口加载失败，请人工接管")

    await entry.click(timeout=3000)
    for _ in range(10):
        active = webim.locator("li.im-session[class*='active']")
        if await active.count():
            return webim
        await page.wait_for_timeout(300)
    raise PlatformActionError("58未能激活当前岗位会话，已停止操作")


async def _webim_scope_matches_job(scope, expected_title: str) -> bool:
    """Only reuse a WebIM shell when its active session can be tied to the job."""
    selectors = (
        "li.im-session[class*='active']",
        ".im-chat-title",
        ".im-header",
        "[class*='session'][class*='active']",
        "[class*='chat-title']",
    )
    fragments: list[str] = []
    for selector in selectors:
        node = scope.locator(selector).first
        try:
            if await node.count():
                value = " ".join((await node.inner_text(timeout=2000)).split()).strip()
                if value:
                    fragments.append(value)
        except Exception:
            continue
    return bool(fragments) and job_titles_match(expected_title, " ".join(fragments))


async def open_verified_58_conversation(
    page,
    *,
    source_url: str,
    thread_url: str | None,
    expected_title: str,
    expected_source_id: str | None,
):
    """Open the stored conversation when verifiable, otherwise activate it from the job page."""
    if thread_url and is_58_webim_url(thread_url):
        try:
            await goto_58_page(page, thread_url)
            await page.wait_for_timeout(1000)
            webim_body = (await page.locator("body").inner_text(timeout=10000))[:50000]
            if any(
                marker.lower() in f"{page.url}\n{webim_body}".lower()
                for marker in LOGIN_MARKERS
            ):
                raise PlatformLoginExpired("58同城登录状态已失效，请重新登录")
            if await _webim_scope_matches_job(page, expected_title):
                return page, False
        except PlatformLoginExpired:
            raise
        except Exception:
            # The shared WebIM shell is best-effort; the verified job page is canonical.
            pass

    await goto_58_page(page, source_url)
    await page.wait_for_timeout(1000)
    body = (await page.locator("body").inner_text(timeout=10000))[:50000]
    if any(marker.lower() in f"{page.url}\n{body}".lower() for marker in LOGIN_MARKERS):
        raise PlatformLoginExpired("58同城登录状态已失效，请重新登录")
    if not page_matches_job(
        expected_source_id=expected_source_id,
        expected_title=expected_title,
        current_url=page.url,
        page_html=(await page.content())[:300000],
        page_text=body,
    ):
        raise PlatformActionError("页面岗位与工作区岗位不一致")
    for label in ("微聊", "在线聊", "聊一聊", "联系HR", "联系招聘者"):
        locator = await first_visible_text(page, label)
        if locator is None:
            continue
        try:
            return await open_58_webim_scope(page, locator), True
        except Exception:
            continue
    raise PlatformActionError("页面未找到可核验的微聊入口，请人工接管")


async def _find_message_nodes(scope):
    selectors = (
        ".im-msg-list > li.im-msg",
        ".im-msg-list [class*='im-msg']",
        "[class*='message-list'] [class*='message-item']",
        "[class*='chat-list'] [data-msgid]",
        "[data-message-id]",
        "[data-msgid]",
    )
    for selector in selectors:
        nodes = scope.locator(selector)
        try:
            count = await nodes.count()
        except Exception:
            continue
        if count:
            return nodes, selector, count
    return scope.locator(".im-msg-list > li.im-msg"), selectors[0], 0


async def _conversation_identity(scope) -> str:
    active = scope.locator(
        "li.im-session[class*='active'], [class*='session'][class*='active']"
    ).first
    if not await active.count():
        return ""
    for attribute in ("data-sessionid", "data-id", "data-infoid", "id"):
        value = (await active.get_attribute(attribute) or "").strip()
        if value:
            return value[:200]
    text = " ".join((await active.inner_text()).split()).strip()
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32] if text else ""


async def _conversation_label(scope) -> str:
    for selector in (
        "li.im-session[class*='active']",
        ".im-chat-title",
        "[class*='session'][class*='active']",
        "[class*='chat-title']",
    ):
        node = scope.locator(selector).first
        try:
            if await node.count():
                value = " ".join((await node.inner_text()).split()).strip()
                if value:
                    return value[:200]
        except Exception:
            continue
    return ""


async def fill_58_chat_editor(scope, content: str) -> None:
    editor = await first_visible_selector(
        scope,
        ".im-input-richtext[contenteditable='true'], textarea, "
        "[contenteditable='true'], input[placeholder*='消息'], input[placeholder*='输入']",
    )
    if editor is not None:
        await editor.fill(content)
        return
    # The embedded WebIM iframe can be visually collapsed in headless mode even
    # though its active conversation and editor are present.
    editor = scope.locator(".im-input-richtext[contenteditable='true']").first
    if not await editor.count():
        raise PlatformActionError("页面未找到聊天输入框，请人工联系")
    await editor.evaluate(
        """(element, value) => {
            element.focus();
            element.innerText = value;
            element.dispatchEvent(new InputEvent('input', {
                bubbles: true, inputType: 'insertText', data: value
            }));
        }""",
        content,
    )
    if content not in (await editor.inner_text()):
        raise PlatformActionError("聊天输入框内容写入失败，已停止操作")


async def apply_job_58(
    *, storage_state: str, source_url: str, expected_title: str, greeting: str,
    resume_file_path: str, resume_file_name: str, resume_file_sha256: str,
    expected_source_id: str | None = None,
) -> dict:
    if not Path(storage_state).is_file():
        raise PlatformLoginExpired("招聘平台登录状态文件不存在，请重新登录")
    if not is_direct_58_job_url(source_url):
        raise PlatformActionError("岗位缺少可核验的58同城详情链接，请手动投递")
    file_path = Path(resume_file_path)
    if not file_path.is_file() or file_path.name != resume_file_name:
        raise PlatformActionError("待投递简历文件不存在或文件名不一致，已停止投递")
    actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
    if actual_hash != resume_file_sha256:
        raise PlatformActionError("待投递简历文件哈希校验失败，已停止投递")

    async with async_playwright() as playwright:
        browser, context = await create_58_browser_context(playwright, storage_state)
        try:
            page = await context.new_page()
            await goto_58_page(page, source_url)
            await page.wait_for_timeout(1000)
            body = (await page.locator("body").inner_text(timeout=10000))[:50000]
            html = (await page.content())[:300000]
            lowered = f"{page.url}\n{body}".lower()
            if any(marker.lower() in lowered for marker in LOGIN_MARKERS):
                raise PlatformLoginExpired("58同城登录状态已失效，请重新登录")
            if not page_matches_job(
                expected_source_id=expected_source_id,
                expected_title=expected_title,
                current_url=page.url,
                page_html=html,
                page_text=body,
            ):
                raise PlatformJobMismatch(
                    "岗位详情已发生变化，请重新获取最新岗位后再投递"
                )
            page_state = classify_job_page(body)
            if page_state == "closed":
                raise PlatformJobClosed("58同城岗位已关闭或下架，已停止操作")
            if page_state == "already_applied":
                return {
                    "final_url": page.url[:500],
                    "evidence": "58页面已申请",
                    "application_status": "already_applied",
                    "resume_delivery_strategy": "previous_application",
                    "resume_verified": False,
                }

            delivery_strategy = await upload_selected_resume(page, resume_file_path)

            # Greeting fields vary between platform versions. Filling is best-effort;
            # clicking and success verification remain strict.
            for selector in ("textarea", "input[placeholder*='打招呼']", "input[placeholder*='留言']"):
                locator = await first_visible_selector(page, selector)
                try:
                    if locator is not None:
                        await locator.fill(greeting[:500])
                        break
                except Exception:
                    continue

            clicked = False
            for label in ("投递简历", "立即申请", "申请职位", "申请岗位"):
                locator = await first_visible_text(page, label)
                try:
                    if locator is not None:
                        await locator.click(timeout=3000)
                        clicked = True
                        break
                except Exception:
                    continue
            if not clicked:
                raise PlatformActionError("页面未找到可核验的投递按钮，请手动投递")

            await page.wait_for_timeout(1200)
            for label in ("确认投递", "确认申请"):
                locator = await first_visible_text(page, label, exact=True)
                try:
                    if locator is not None:
                        await locator.click(timeout=3000)
                        await page.wait_for_timeout(1200)
                        break
                except Exception:
                    continue

            final_body = (await page.locator("body").inner_text(timeout=10000))[:50000]
            final_lowered = f"{page.url}\n{final_body}".lower()
            if any(marker.lower() in final_lowered for marker in LOGIN_MARKERS):
                raise PlatformLoginExpired("58同城登录状态已失效，请重新登录")
            evidence = next((marker for marker in SUCCESS_MARKERS if marker in final_body), None)
            if not evidence:
                raise PlatformActionError("平台未返回明确的投递成功提示，未记录为成功")
            return {
                "final_url": page.url[:500],
                "evidence": evidence,
                "application_status": "submitted",
                "resume_delivery_strategy": delivery_strategy,
                "resume_verified": True,
            }
        finally:
            await close_58_browser_context(browser, context)


async def send_message_58(
    *, storage_state: str, source_url: str, thread_url: str | None,
    expected_title: str, content: str, expected_source_id: str | None = None,
) -> dict:
    """Send one user-approved message and verify it appears in the conversation."""
    if not Path(storage_state).is_file():
        raise PlatformLoginExpired("招聘平台登录状态文件不存在，请重新登录")
    if not is_direct_58_job_url(source_url):
        raise PlatformActionError("岗位缺少可核验的58同城详情链接，请人工联系HR")

    async with async_playwright() as playwright:
        browser, context = await create_58_browser_context(playwright, storage_state)
        try:
            page = await context.new_page()
            scope, opened_inline = await open_verified_58_conversation(
                page,
                source_url=source_url,
                thread_url=thread_url,
                expected_title=expected_title,
                expected_source_id=expected_source_id,
            )

            before_body = (await scope.locator("body").inner_text(timeout=10000))[:50000]
            before_count = before_body.count(content)
            await fill_58_chat_editor(scope, content)
            sent = False
            for label in ("发送", "发 送"):
                button = await first_visible_text(scope, label, exact=True)
                try:
                    if button is not None:
                        await button.click(timeout=3000)
                        sent = True
                        break
                except Exception:
                    continue
            if not sent:
                button = scope.locator(".im-send").first
                if await button.count():
                    await button.evaluate("element => element.click()")
                    sent = True
            if not sent:
                raise PlatformActionError("页面未找到明确的发送按钮，已停止操作")
            after_body = ""
            for _ in range(12):
                await page.wait_for_timeout(700)
                after_body = (
                    await scope.locator("body").inner_text(timeout=10000)
                )[:50000]
                if after_body.count(content) > before_count:
                    break
            final_lowered = f"{page.url}\n{after_body}".lower()
            if any(marker.lower() in final_lowered for marker in LOGIN_MARKERS):
                raise PlatformLoginExpired("58同城登录状态已失效，请重新登录")
            if after_body.count(content) <= before_count and "发送成功" not in after_body:
                raise PlatformActionError("平台未返回消息已发送的可核验证据，未记录为成功")
            return {
                "thread_url": scope.url[:500] if opened_inline else page.url[:500],
                "thread_inline": opened_inline,
                "conversation_id": await _conversation_identity(scope),
                "conversation_label": await _conversation_label(scope),
                "evidence": "消息已出现在会话中",
            }
        finally:
            await close_58_browser_context(browser, context)


async def read_messages_58(
    *, storage_state: str, source_url: str, thread_url: str | None, expected_title: str,
    expected_source_id: str | None = None,
) -> dict:
    """Read only sender-identifiable messages; ambiguous DOM nodes are ignored."""
    if not Path(storage_state).is_file():
        raise PlatformLoginExpired("招聘平台登录状态文件不存在，请重新登录")
    if not is_direct_58_job_url(source_url):
        raise PlatformActionError("岗位缺少可核验的58同城详情链接")
    async with async_playwright() as playwright:
        browser, context = await create_58_browser_context(playwright, storage_state)
        try:
            page = await context.new_page()
            scope, opened_inline = await open_verified_58_conversation(
                page,
                source_url=source_url,
                thread_url=thread_url,
                expected_title=expected_title,
                expected_source_id=expected_source_id,
            )
            messages: list[dict] = []
            nodes, selector_used, node_count = await _find_message_nodes(scope)
            if node_count == 0:
                structure = scope.locator(
                    ".im-msg-list, [class*='message-list'], [class*='chat-list'], "
                    ".im-input-richtext, [contenteditable='true']"
                )
                active_session = scope.locator(
                    "li.im-session[class*='active'], [class*='session'][class*='active']"
                )
                if not await structure.count() and not await active_session.count():
                    raise PlatformActionError(
                        "58微聊已打开，但没有识别到消息区域；页面结构可能已更新"
                    )
            for index in range(min(node_count, 100)):
                node = nodes.nth(index)
                try:
                    class_name = await node.get_attribute("class") or ""
                    if "im-msg-tip" in class_name:
                        continue
                    sender = (
                        "user"
                        if "im-msg-me" in class_name
                        else infer_message_sender_from_class(class_name)
                    )
                    if sender is None and "im-msg" in class_name:
                        sender = "hr"
                    content_node = node.locator(
                        ".im-msg-content, [class*='message-content'], "
                        "[class*='msg-content'], .content"
                    ).first
                    if not await content_node.count():
                        continue
                    content = " ".join((await content_node.inner_text()).split()).strip()
                    platform_message_id = ""
                    for attribute in (
                        "data-msgid", "data-message-id", "data-id", "msgid", "id",
                    ):
                        platform_message_id = (
                            await node.get_attribute(attribute) or ""
                        ).strip()
                        if platform_message_id:
                            break
                    if not platform_message_id:
                        identity_node = node.locator(
                            "[data-msgid], [data-message-id], [data-id], [msgid]"
                        ).first
                        if await identity_node.count():
                            for attribute in (
                                "data-msgid", "data-message-id", "data-id", "msgid",
                            ):
                                platform_message_id = (
                                    await identity_node.get_attribute(attribute) or ""
                                ).strip()
                                if platform_message_id:
                                    break
                    message_time = ""
                    for attribute in (
                        "data-time", "data-timestamp", "data-send-time", "timestamp",
                    ):
                        message_time = (await node.get_attribute(attribute) or "").strip()
                        if message_time:
                            break
                    if not message_time:
                        time_node = node.locator(
                            ".im-msg-time, .im-msg-date, .msg-time, time, "
                            "[data-time], [data-timestamp]"
                        ).first
                        if await time_node.count():
                            for attribute in (
                                "datetime", "data-time", "data-timestamp", "title",
                            ):
                                message_time = (
                                    await time_node.get_attribute(attribute) or ""
                                ).strip()
                                if message_time:
                                    break
                            if not message_time:
                                message_time = " ".join(
                                    (await time_node.inner_text()).split()
                                ).strip()
                    if not message_time:
                        preceding_time = node.locator(
                            "xpath=preceding-sibling::li[contains(@class,'im-msg-tip')][1]"
                        )
                        if await preceding_time.count():
                            message_time = " ".join(
                                (await preceding_time.inner_text()).split()
                            ).strip()
                except Exception:
                    continue
                if sender and content:
                    messages.append({
                        "sender_type": sender,
                        "content": content[:2000],
                        "platform_message_id": platform_message_id[:200],
                        "message_time": message_time[:100],
                        "position": index,
                    })
            return {
                "thread_url": scope.url[:500] if opened_inline else page.url[:500],
                "thread_inline": opened_inline,
                "conversation_id": await _conversation_identity(scope),
                "conversation_label": await _conversation_label(scope),
                "selector_used": selector_used,
                "message_node_count": node_count,
                "messages": messages,
            }
        finally:
            await close_58_browser_context(browser, context)
