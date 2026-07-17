from pathlib import Path

import pytest
from playwright.async_api import async_playwright

from app.crawlers.job_58_playwright import Job58PlaywrightCrawler


FIXTURE = Path(__file__).parent / "fixtures" / "58_job_list_real_fragment.html"


@pytest.mark.asyncio
async def test_real_58_html_fragment_is_parsed_with_locator_protocol():
    html = FIXTURE.read_text(encoding="utf-8")
    crawler = Job58PlaywrightCrawler()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.set_content(html)
            rows, fallback, invalid = await crawler._extract_rows(page)
        finally:
            await browser.close()

    assert fallback is False
    assert invalid == 0
    assert len(rows) == 2
    assert rows[0]["title"] == "Python后端开发工程师"
    assert rows[0]["area"] == "海淀"
    assert rows[0]["company"] == "北京示例科技有限公司"
    assert rows[0]["entinfo"] == "63689817698991"
    assert rows[0]["salary"] == "8000-12000元/月"

    job = crawler._row_to_job(rows[0], "北京", "https://bj.58.com/job/", "Python后端开发")
    assert job is not None
    assert job["source_id"] == "63689817698991"
    assert job["title"] == "Python后端开发工程师"
    assert job["salary_min"] == 8000
    assert job["salary_max"] == 12000


@pytest.mark.asyncio
async def test_58_fallback_recommendations_are_not_treated_as_search_results():
    html = """
    <ul id="list_con">
      <li class="job_item">暂无相关职位，为您提供以下职位</li>
      <li class="job_item">
        <div class="job_name" sortid="100"><a href="https://bj.58.com/100x.shtml">办公室文员</a></div>
        <div class="comp_name"><a title="示例公司">示例公司</a></div>
        <p class="job_require"><span class="cate">文员</span></p>
        <a class="apply" infoid="12345678901">申请</a>
      </li>
    </ul>
    """
    crawler = Job58PlaywrightCrawler()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.set_content(html)
            rows, fallback, invalid = await crawler._extract_rows(page)
        finally:
            await browser.close()

    assert fallback is True
    assert rows == []
    assert invalid == 0


def test_known_technical_roles_use_58_category_routes():
    crawler = Job58PlaywrightCrawler()

    assert crawler._known_category_url("xa", "Python后端开发工程师") == (
        "https://xa.58.com/npythonkf?fullPath=674,413795,413796,413801&sort=time"
    )
    assert crawler._known_category_url("nj", "Java开发工程师") == (
        "https://nj.58.com/njavakf?fullPath=674,413795,413796,413797&sort=time"
    )
    assert crawler._known_category_urls("xa", "Python后端开发工程师") == [
        "https://xa.58.com/npythonkf?fullPath=674,413795,413796,413801&sort=time",
        "https://xa.58.com/ruanjianyf?fullPath=674,413795,413796&sort=time",
    ]
    assert crawler._known_category_url("bj", "厨师") is None

    assert crawler._matches_parent_direction(
        {"title": "后端开发工程师", "cate": "软件研发"}, "Python后端开发"
    ) is True
    assert crawler._matches_parent_direction(
        {"title": "C++开发工程师", "cate": "软件研发"}, "Python后端开发"
    ) is False


@pytest.mark.asyncio
async def test_custom_role_can_discover_category_route_from_58_navigation():
    html = """
    <nav>
      <a data-action="https://xa.58.com/nwebqd?fullPath=674,413795,413796,413805"
         data-catename="Web前端">Web前端</a>
      <a data-action="https://xa.58.com/dianshangyy?fullPath=674,100,200"
         data-catename="电商运营">电商运营</a>
      <a data-action="https://bj.58.com/dianshangyy?fullPath=674,100,200"
         data-catename="电商运营">其他城市</a>
    </nav>
    """
    crawler = Job58PlaywrightCrawler()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.set_content(html)
            url = await crawler._discover_category_url(page, "电商运营专员", "xa")
        finally:
            await browser.close()

    assert url == "https://xa.58.com/dianshangyy?fullPath=674,100,200&sort=time"
