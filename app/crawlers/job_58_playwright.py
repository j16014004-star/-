"""基于登录态的 58 同城 Playwright 采集器。"""
import re
from difflib import SequenceMatcher
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from playwright.async_api import Error as PlaywrightError, Page, async_playwright

from app.core.config import settings
from app.services.platform_session_service import load_storage_state
from app.crawlers.base import BaseCrawler


class LoginExpiredError(Exception):
    """平台登录态失效或需要用户再次验证。"""


class JobPageParseError(RuntimeError):
    """页面存在岗位节点，但当前解析器无法提取有效岗位。"""

    def __init__(self, message: str, diagnostics: dict | None = None) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics or {}


class NetworkAccessDeniedError(RuntimeError):
    """The runtime or browser policy denied outbound access to 58."""


# 调试目录：logs/crawl_debug/，仅本地排查用，不入库、不返回前端
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEBUG_DIR = PROJECT_ROOT / "logs" / "crawl_debug"

# 岗位列表容器：58 搜索结果服务端渲染，稳定存在 li.job_item
LIST_ITEM_SELECTOR = "#list_con li.job_item"

# 软拦截特征（仅在列表为空时判定，避免误伤页脚“安全中心”等正常文案）
BLOCK_TEXT_MARKERS = ("安全验证", "滑动验证", "请拖动", "拖动滑块", "点击完成验证", "访问过于频繁")
NO_RESULT_MARKERS = ("暂无相关职位", "为您提供以下职位", "没有找到相关职位")

# 58 对部分技术岗位使用独立分类页，通用 ?key= 搜索可能错误返回“其他岗位”。
# 路由和 fullPath 来自 58 岗位分类导航；城市子域在运行时替换。
CATEGORY_ROUTES = (
    (("python", "fastapi", "django", "flask"), "npythonkf", "674,413795,413796,413801"),
    (("java", "spring"), "njavakf", "674,413795,413796,413797"),
    (("web前端", "前端开发", "vue", "react", "javascript", "typescript"),
     "nwebqd", "674,413795,413796,413805"),
    (("数据分析", "数据分析师", "pandas"), "shujufxsh", "674,413795,413957,413962"),
    (("数据运营",), "shujuyy", "674,413246,413287,413329"),
)

# 精确技术分类无岗位时继续访问上级分类；最终仍由岗位匹配规则过滤方向。
PARENT_CATEGORY_ROUTES = (
    (("python", "fastapi", "django", "flask", "java", "spring", "web前端", "前端开发",
      "vue", "react", "javascript", "typescript", "后端开发"),
     "ruanjianyf", "674,413795,413796"),
    (("数据分析", "数据分析师", "pandas", "数据开发"),
     "shujukffx", "674,413795,413957"),
)

PARENT_DIRECTION_TERMS = (
    (("python", "fastapi", "django", "flask"), ("python", "后端", "服务端", "django", "fastapi")),
    (("java", "spring"), ("java", "后端", "服务端", "spring")),
    (("web前端", "前端开发", "vue", "react", "javascript", "typescript"),
     ("前端", "web", "vue", "react", "javascript", "typescript")),
    (("数据分析", "数据分析师", "pandas", "数据开发"),
     ("数据分析", "数据开发", "数据运营", "数据专员")),
)


def _safe_name(text: str) -> str:
    """把关键词转成安全的文件名片段。"""
    return "".join(c if c.isalnum() else "_" for c in text)[:30] or "kw"


class Job58PlaywrightCrawler(BaseCrawler):
    """只使用用户已登录 storage state 的低频岗位采集器。"""

    SOURCE = "58"
    SOURCE_NAME = "58同城"
    CITY_CODES = {
        "北京": "bj", "上海": "sh", "广州": "gz", "深圳": "sz", "杭州": "hz",
        "成都": "cd", "西安": "xa", "武汉": "wh", "南京": "nj", "重庆": "cq",
        "苏州": "su", "天津": "tj", "郑州": "zz", "东莞": "dg", "青岛": "qd",
        "沈阳": "sy", "宁波": "nb", "昆明": "km", "大连": "dl", "长沙": "cs",
    }

    def __init__(self) -> None:
        self.last_diagnostics: dict = {}

    async def crawl(self, storage_state: str, keywords: list[str], limit: int, city: str = "北京") -> list[dict]:
        if not keywords:
            return []
        results: list[dict] = []
        seen_ids: set[str] = set()
        city_name = city if city in self.CITY_CODES else "北京"
        city_code = self.CITY_CODES.get(city_name, "bj")
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
        diagnostics = {
            "query_count": 0,
            "category_queries": 0,
            "keyword_queries": 0,
            "discovered_categories": 0,
            "direction_filtered_items": 0,
            "raw_items": 0,
            "parsed_items": 0,
            "accepted_items": 0,
            "invalid_items": 0,
            "duplicate_items": 0,
            "no_result_queries": 0,
        }
        print(f"[crawl] start city={city_name}({city_code}) keywords={keywords[:5]} limit={limit}", flush=True)

        async with async_playwright() as playwright:
            endpoint = settings.PLAYWRIGHT_CDP_ENDPOINT.strip()
            browser = (
                await playwright.chromium.connect_over_cdp(endpoint)
                if endpoint
                else await playwright.chromium.launch(
                    headless=settings.PLAYWRIGHT_CRAWL_HEADLESS
                )
            )
            context = await browser.new_context(
                storage_state=load_storage_state(storage_state),
                viewport={"width": 1366, "height": 768},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()
            try:
                search_targets: list[tuple[str, str, str]] = []
                planned_urls: set[str] = set()
                for keyword in keywords[:5]:
                    for category_index, category_url in enumerate(
                        self._known_category_urls(city_code, keyword)
                    ):
                        if category_url not in planned_urls:
                            search_kind = "category" if category_index == 0 else "parent"
                            search_targets.append((keyword, category_url, search_kind))
                            planned_urls.add(category_url)
                    keyword_url = self._keyword_search_url(city_code, keyword)
                    if keyword_url not in planned_urls:
                        search_targets.append((keyword, keyword_url, "keyword"))
                        planned_urls.add(keyword_url)

                target_index = 0
                max_queries = max(1, min(12, settings.JOB_CRAWL_MAX_QUERIES))
                early_stop_count = max(
                    1, min(limit, round(limit * settings.JOB_CRAWL_EARLY_STOP_RATIO))
                )
                while target_index < len(search_targets) and diagnostics["query_count"] < max_queries:
                    if len(results) >= early_stop_count:
                        break
                    keyword, url, search_kind = search_targets[target_index]
                    idx = target_index
                    target_index += 1
                    diagnostics["query_count"] += 1
                    diagnostics["keyword_queries" if search_kind == "keyword" else "category_queries"] += 1
                    try:
                        await page.goto(
                            url,
                            wait_until="domcontentloaded",
                            timeout=max(5, settings.JOB_CRAWL_PAGE_TIMEOUT_SECONDS) * 1000,
                        )
                    except PlaywrightError as exc:
                        detail = str(exc).strip()
                        if "err_network_access_denied" in detail.lower():
                            raise NetworkAccessDeniedError(
                                "运行环境无法访问58同城（ERR_NETWORK_ACCESS_DENIED），"
                                "请放行Python/Chromium访问*.58.com后重试"
                            ) from exc
                        raise
                    final_url = page.url
                    if self._looks_blocked_url(final_url):
                        await self._dump_debug(page, run_tag, idx, keyword, final_url, note="blocked_url")
                        raise LoginExpiredError("平台登录态失效或需要人工验证")

                    item_count = await self._wait_for_items(page)
                    rows, fallback_results, invalid_rows = await self._extract_rows(page)
                    diagnostics["raw_items"] += item_count
                    diagnostics["invalid_items"] += invalid_rows

                    if fallback_results:
                        diagnostics["no_result_queries"] += 1
                        if search_kind == "keyword":
                            discovered_url = await self._discover_category_url(page, keyword, city_code)
                            if discovered_url and discovered_url not in planned_urls:
                                search_targets.insert(
                                    target_index, (keyword, discovered_url, "category")
                                )
                                planned_urls.add(discovered_url)
                                diagnostics["discovered_categories"] += 1
                        rows = []

                    if item_count == 0:
                        body_text = await self._text(page.locator("body"))
                        note = "empty_list"
                        if any(marker in body_text for marker in BLOCK_TEXT_MARKERS):
                            note = "blocked_text"
                            await self._dump_debug(page, run_tag, idx, keyword, final_url, note=note)
                            raise LoginExpiredError("平台要求人工验证，登录态可能已失效")
                        await self._dump_debug(page, run_tag, idx, keyword, final_url, note=note)

                    if item_count > 0 and not rows and not fallback_results:
                        await self._dump_debug(
                            page, run_tag, idx, keyword, final_url, note="parse_failed"
                        )
                        self.last_diagnostics = diagnostics
                        raise JobPageParseError(
                            f"58页面检测到 {item_count} 个岗位节点，但未解析出有效岗位",
                            diagnostics.copy(),
                        )

                    diagnostics["parsed_items"] += len(rows)

                    print(
                        f"[crawl] kw='{keyword}' url={final_url} waited_items={item_count} rows={len(rows)}",
                        flush=True,
                    )

                    processed_count = 0
                    accepted_count = 0
                    invalid_count = 0
                    duplicate_count = 0
                    for row in rows:
                        if len(results) >= limit:
                            break
                        processed_count += 1
                        if search_kind == "parent" and not self._matches_parent_direction(row, keyword):
                            diagnostics["direction_filtered_items"] += 1
                            continue
                        job = self._row_to_job(row, city_name, final_url, keyword)
                        if not job:
                            invalid_count += 1
                            continue
                        if job["source_id"] in seen_ids:
                            duplicate_count += 1
                            continue
                        seen_ids.add(job["source_id"])
                        results.append(job)
                        accepted_count += 1

                    diagnostics["accepted_items"] += accepted_count
                    diagnostics["invalid_items"] += invalid_count
                    diagnostics["duplicate_items"] += duplicate_count

                    print(
                        f"[crawl] kw='{keyword}' processed={processed_count} accepted={accepted_count} "
                        f"invalid={invalid_count} duplicate={duplicate_count}",
                        flush=True,
                    )
                    if rows and accepted_count == 0:
                        sample_rows = [
                            {
                                key: str(row.get(key) or "")[:120]
                                for key in ("title", "cate", "entinfo", "sortid")
                            }
                            for row in rows[:3]
                            if isinstance(row, dict)
                        ]
                        print(
                            f"[crawl] kw='{keyword}' no_jobs sample_rows={sample_rows}",
                            flush=True,
                        )
                        await self._dump_debug(
                            page, run_tag, idx, keyword, final_url, note="rows_but_no_jobs"
                        )
            finally:
                await context.close()
                if not endpoint:
                    await browser.close()
        self.last_diagnostics = diagnostics
        print(f"[crawl] done total_jobs={len(results)}", flush=True)
        return results

    @staticmethod
    def _keyword_search_url(city_code: str, keyword: str) -> str:
        return f"https://{city_code}.58.com/job/?key={quote(keyword)}&final=1&sort=time"

    @staticmethod
    def _known_category_url(city_code: str, keyword: str) -> str | None:
        urls = Job58PlaywrightCrawler._known_category_urls(city_code, keyword)
        return urls[0] if urls else None

    @staticmethod
    def _known_category_urls(city_code: str, keyword: str) -> list[str]:
        normalized = Job58PlaywrightCrawler._normalize_role_text(keyword)
        urls: list[str] = []
        for markers, route, full_path in CATEGORY_ROUTES:
            if any(Job58PlaywrightCrawler._normalize_role_text(marker) in normalized for marker in markers):
                urls.append(f"https://{city_code}.58.com/{route}?fullPath={full_path}&sort=time")
                break
        for markers, route, full_path in PARENT_CATEGORY_ROUTES:
            if any(Job58PlaywrightCrawler._normalize_role_text(marker) in normalized for marker in markers):
                urls.append(f"https://{city_code}.58.com/{route}?fullPath={full_path}&sort=time")
                break
        return urls

    async def _discover_category_url(self, page: Page, keyword: str, city_code: str) -> str | None:
        """从58分类导航中识别用户自定义岗位对应的分类页。"""
        try:
            categories = await page.locator("a[data-action][data-catename]").evaluate_all(
                """nodes => nodes.map(node => ({
                    name: node.getAttribute('data-catename') || '',
                    url: node.getAttribute('data-action') || ''
                }))"""
            )
        except Exception:
            return None

        target = self._normalize_role_text(keyword)
        if not target:
            return None
        best_url = ""
        best_score = 0.0
        expected_prefix = f"https://{city_code}.58.com/"
        for category in categories:
            name = self._normalize_role_text(str(category.get("name") or ""))
            url = str(category.get("url") or "").strip()
            if not name or not url.startswith(expected_prefix):
                continue
            if name == target:
                score = 1.0
            elif len(name) >= 2 and (name in target or target in name):
                score = 0.9
            else:
                score = SequenceMatcher(None, target, name).ratio()
            if score > best_score:
                best_score = score
                best_url = url

        # 阈值保持严格，防止“Python开发”被误映射到其他开发分类。
        if best_score < 0.72:
            return None
        separator = "&" if "?" in best_url else "?"
        return f"{best_url}{separator}sort=time"

    @staticmethod
    def _normalize_role_text(value: str) -> str:
        return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", (value or "").lower())

    @staticmethod
    def _matches_parent_direction(row: dict, keyword: str) -> bool:
        target = Job58PlaywrightCrawler._normalize_role_text(keyword)
        content = Job58PlaywrightCrawler._normalize_role_text(
            f"{row.get('title') or ''} {row.get('cate') or ''}"
        )
        for markers, terms in PARENT_DIRECTION_TERMS:
            if any(Job58PlaywrightCrawler._normalize_role_text(marker) in target for marker in markers):
                return any(
                    Job58PlaywrightCrawler._normalize_role_text(term) in content
                    for term in terms
                )
        return False

    async def _wait_for_items(self, page: Page) -> int:
        """等岗位列表和关键文本真正出现，返回等到的条数。"""
        try:
            await page.locator(LIST_ITEM_SELECTOR).first.wait_for(
                timeout=max(2, settings.JOB_CRAWL_ITEM_WAIT_SECONDS) * 1000,
                state="attached",
            )
        except Exception:
            pass
        return await page.locator(LIST_ITEM_SELECTOR).count()

    async def _extract_rows(self, page: Page) -> tuple[list[dict], bool, int]:
        """通过 Playwright Locator 协议逐项提取，避开站点脚本对页面主环境的干扰。"""
        items = page.locator(LIST_ITEM_SELECTOR)
        count = await items.count()
        rows: list[dict] = []
        invalid_rows = 0
        fallback_results = False

        for index in range(count):
            item = items.nth(index)
            raw_text = await self._text(item)
            if any(marker in raw_text for marker in NO_RESULT_MARKERS):
                fallback_results = True
                continue

            name = item.locator(".job_name").first
            link = item.locator(".job_name a").first
            apply_link = item.locator("a.apply[infoid]").first
            company_link = item.locator(".comp_name a").first
            raw_title = await self._text(link) or await self._text(name)
            area, title = self._split_title(raw_title)
            href = await self._attribute(link, "href")
            urlparams = await self._attribute(link, "urlparams")
            apply_infoid = await self._attribute(apply_link, "infoid")
            sortid = await self._attribute(name, "sortid")
            entinfo = self._extract_info_id(href, urlparams, apply_infoid)
            cate = await self._text(item.locator(".job_require .cate").first)

            if not (title or cate) or not (entinfo or sortid):
                invalid_rows += 1
                continue

            rows.append({
                "title": title,
                "area": area,
                "raw_title": raw_title,
                "salary": await self._text(item.locator(".job_salary").first),
                "welfare": await self._text(item.locator(".job_wel").first),
                "company": (
                    await self._attribute(company_link, "title")
                    or await self._text(company_link)
                    or await self._text(item.locator(".comp_name").first)
                ),
                "company_href": await self._attribute(company_link, "href"),
                "cate": cate,
                "education": await self._text(item.locator(".job_require .xueli").first),
                "experience": await self._text(item.locator(".job_require .jingyan").first),
                "href": href,
                "sortid": sortid,
                "entinfo": entinfo,
            })

        # 58 在精准搜索无结果时会追加其他岗位；整页必须按“无精准结果”处理。
        return ([] if fallback_results else rows), fallback_results, invalid_rows

    @staticmethod
    async def _text(locator) -> str:
        try:
            if await locator.count() == 0:
                return ""
            return " ".join((await locator.text_content() or "").split())
        except Exception:
            return ""

    @staticmethod
    async def _attribute(locator, name: str) -> str:
        try:
            if await locator.count() == 0:
                return ""
            return (await locator.get_attribute(name) or "").strip()
        except Exception:
            return ""

    @staticmethod
    def _split_title(value: str) -> tuple[str, str]:
        parts = [item.strip() for item in value.split("|") if item.strip()]
        if len(parts) >= 2:
            return parts[0], " | ".join(parts[1:])
        return "", value.strip()

    @staticmethod
    def _extract_info_id(*values: str) -> str:
        combined = "&".join(value or "" for value in values)
        match = re.search(r"(?:entinfo|infoid)=([0-9]+)|(?:^|&)([0-9]{8,})(?:_|&|$)", combined)
        if not match:
            direct = re.search(r"[0-9]{8,}", values[-1] if values else "")
            return direct.group(0) if direct else ""
        return match.group(1) or match.group(2) or ""

    @staticmethod
    def _looks_blocked_url(url: str) -> bool:
        lowered = url.lower()
        return any(marker in lowered for marker in ("passport", "verify", "antibot", "callback.58"))

    def _row_to_job(self, row: dict, city: str, search_url: str, keyword: str = "") -> dict | None:
        """把列表项字典转成入库用的岗位记录。"""
        title = (row.get("title") or row.get("cate") or "").strip()[:200]
        if not title:
            return None
        # 稳定 id：优先真实 infoid(entinfo)，回退 sortid
        source_id = (row.get("entinfo") or "").strip() or f"sid_{(row.get('sortid') or '').strip()}"
        if source_id in ("", "sid_"):
            return None

        salary_min, salary_max = self.normalize_salary(row.get("salary") or "")
        company = (row.get("company") or "").strip()[:200] or "58同城岗位"
        welfare = (row.get("welfare") or "").strip()
        cate = (row.get("cate") or "").strip()
        education = (row.get("education") or "").strip()[:50] or None
        experience = (row.get("experience") or "").strip()[:50] or None

        # source_url 列限长 500：legoclick 跳转链常超长，超限回退到搜索页
        href = (row.get("href") or "").strip()
        source_url = href if href.startswith("http") and len(href) <= 500 else search_url

        desc_parts = [p for p in (cate, welfare, f"经验:{experience}" if experience else "",
                                  f"学历:{education}" if education else "") if p]
        description = " | ".join(desc_parts)[:5000]
        skills = self.extract_skills_from_text(f"{title} {cate} {welfare}")

        return {
            "source_id": source_id,
            "source": self.SOURCE,
            "source_name": self.SOURCE_NAME,
            "source_url": source_url,
            "company": company,
            "company_logo": None,
            "title": title,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "city": city,
            "area": (row.get("area") or "").strip()[:100] or None,
            "experience_required": experience,
            "education_required": education,
            "skills": skills,
            "description": description,
            "is_active": True,
            "crawl_time": datetime.now(timezone.utc),
        }

    async def _dump_debug(self, page, run_tag: str, idx: int, keyword: str, final_url: str, note: str = "") -> None:
        """把当前页面截图 + HTML + URL 落盘，供人工核对真实结构。"""
        try:
            stem = f"{run_tag}_{idx:02d}_{_safe_name(keyword)}"
            await page.screenshot(path=str(DEBUG_DIR / f"{stem}.png"), full_page=True)
            (DEBUG_DIR / f"{stem}.html").write_text(await page.content(), encoding="utf-8")
            (DEBUG_DIR / f"{stem}.url.txt").write_text(
                f"keyword={keyword}\nfinal_url={final_url}\n{note}\n", encoding="utf-8"
            )
        except Exception as exc:  # 调试落盘失败不影响采集主流程
            print(f"[crawl] dump_debug failed: {exc}", flush=True)
