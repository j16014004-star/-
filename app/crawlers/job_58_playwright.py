"""基于登录态的 58 同城 Playwright 采集器。"""
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from playwright.async_api import async_playwright

from app.core.config import settings
from app.crawlers.base import BaseCrawler


class LoginExpiredError(Exception):
    """平台登录态失效或需要用户再次验证。"""


# 调试目录：logs/crawl_debug/，仅本地排查用，不入库、不返回前端
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEBUG_DIR = PROJECT_ROOT / "logs" / "crawl_debug"

# 岗位列表容器：58 搜索结果服务端渲染，稳定存在 li.job_item
LIST_ITEM_SELECTOR = "#list_con li.job_item"

# 软拦截特征（仅在列表为空时判定，避免误伤页脚“安全中心”等正常文案）
BLOCK_TEXT_MARKERS = ("安全验证", "滑动验证", "请拖动", "拖动滑块", "点击完成验证", "访问过于频繁")
# 直接从列表项结构化提取，不再逐个打开详情页（快、稳、请求量降到 1/36）
EXTRACT_JS = """
() => {
  const clean = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  // 无头模式下不可见元素的 innerText 会返回空串，必须用 textContent/属性兜底
  const txt = (el) => el ? (el.textContent || el.innerText || el.getAttribute('title') || '') : '';
  const attr = (el, name) => el ? (el.getAttribute(name) || '') : '';
  const titleParts = (value) => {
    const raw = clean(value);
    const parts = raw.split('|').map((item) => clean(item)).filter(Boolean);
    if (parts.length >= 2) {
      return {area: parts[0], title: parts.slice(1).join(' | ')};
    }
    return {area: '', title: raw};
  };
  const items = Array.from(document.querySelectorAll('#list_con li.job_item'));
  const rows = items.map((li) => {
    const nameEl = li.querySelector('.job_name');
    const link = li.querySelector('.job_name a') || li.querySelector('a[href]');
    const apply = li.querySelector('a.apply[infoid]');
    const companyEl = li.querySelector('.comp_name a') || li.querySelector('.comp_name');
    const href = link ? (link.href || '') : '';
    const sortid = (nameEl && nameEl.getAttribute('sortid')) || '';
    const linkText = clean(txt(link) || txt(nameEl));
    const parsedTitle = titleParts(linkText);
    let entinfo = '';
    const m = (href + '&' + attr(link, 'urlparams') + '&' + attr(apply, 'infoid')).match(/(?:entinfo|infoid)=([0-9]+)/);
    if (m) entinfo = m[1];
    if (!entinfo) {
      const applyInfoid = attr(apply, 'infoid').match(/[0-9]+/);
      if (applyInfoid) entinfo = applyInfoid[0];
    }
    return {
      title: parsedTitle.title,
      area: parsedTitle.area,
      raw_title: linkText,
      salary: clean(txt(li.querySelector('.job_salary'))),
      welfare: clean(txt(li.querySelector('.job_wel'))),
      company: clean(attr(companyEl, 'title') || txt(companyEl)),
      company_href: (li.querySelector('.comp_name a') || {}).href || '',
      cate: clean(txt(li.querySelector('.job_require .cate'))),
      education: clean(txt(li.querySelector('.job_require .xueli'))),
      experience: clean(txt(li.querySelector('.job_require .jingyan'))),
      href: href,
      sortid: sortid,
      entinfo: entinfo,
    };
  });
  const bodyTxt = document.body.textContent || '';
  return {count: rows.length, rows: rows, bodyLen: bodyTxt.length,
          bodyText: bodyTxt.slice(0, 1500)};
}
"""


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

    async def crawl(self, storage_state: str, skills: list[str], limit: int, city: str = "北京") -> list[dict]:
        if not skills:
            return []
        results: list[dict] = []
        seen_ids: set[str] = set()
        city_name = city if city in self.CITY_CODES else "北京"
        city_code = self.CITY_CODES.get(city_name, "bj")
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"[crawl] start city={city_name}({city_code}) skills={skills[:5]} limit={limit}", flush=True)

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=settings.PLAYWRIGHT_CRAWL_HEADLESS)
            context = await browser.new_context(
                storage_state=storage_state,
                viewport={"width": 1366, "height": 768},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()
            try:
                for idx, keyword in enumerate(skills[:5]):
                    if len(results) >= limit:
                        break
                    url = f"https://{city_code}.58.com/job/?key={quote(keyword)}&final=1&sort=time"
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    final_url = page.url
                    if self._looks_blocked_url(final_url):
                        await self._dump_debug(page, run_tag, idx, keyword, final_url, note="blocked_url")
                        raise LoginExpiredError("平台登录态失效或需要人工验证")

                    item_count = await self._wait_for_items(page)
                    payload = await page.evaluate(EXTRACT_JS)
                    rows = payload.get("rows", [])

                    if not rows:
                        body_text = payload.get("bodyText", "")
                        note = "empty_list"
                        if any(marker in body_text for marker in BLOCK_TEXT_MARKERS):
                            note = "blocked_text"
                            await self._dump_debug(page, run_tag, idx, keyword, final_url, note=note)
                            raise LoginExpiredError("平台要求人工验证，登录态可能已失效")
                        await self._dump_debug(page, run_tag, idx, keyword, final_url, note=note)

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
                await browser.close()
        print(f"[crawl] done total_jobs={len(results)}", flush=True)
        return results

    async def _wait_for_items(self, page) -> int:
        """等岗位列表和关键文本真正出现，返回等到的条数。"""
        try:
            await page.wait_for_selector(LIST_ITEM_SELECTOR, timeout=8000, state="attached")
        except Exception:
            pass
        try:
            await page.wait_for_function(
                """
                () => Array.from(document.querySelectorAll('#list_con li.job_item'))
                  .some((li) => {
                    const title = (li.querySelector('.job_name a')?.textContent || '').trim();
                    const cate = (li.querySelector('.job_require .cate')?.textContent || '').trim();
                    return title || cate;
                  })
                """,
                timeout=5000,
            )
        except Exception:
            pass
        try:
            return await page.evaluate(
                "() => document.querySelectorAll('#list_con li.job_item').length"
            )
        except Exception:
            return 0

    @staticmethod
    def _looks_blocked_url(url: str) -> bool:
        lowered = url.lower()
        return any(marker in lowered for marker in ("passport", "verify", "antibot", "callback.58"))

    def _row_to_job(self, row: dict, city: str, search_url: str, keyword: str = "") -> dict | None:
        """把列表项字典转成入库用的岗位记录。"""
        title = (row.get("title") or row.get("cate") or keyword or "").strip()[:200]
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
