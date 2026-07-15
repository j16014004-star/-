"""
58同城岗位爬虫
"""
import re
import logging
from datetime import datetime, timezone
from urllib.parse import quote

from app.crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)


class Job58Crawler(BaseCrawler):
    """58同城岗位爬虫"""

    SOURCE = "58"
    SOURCE_NAME = "58同城"

    # 城市代码映射
    CITY_CODES = {
        "北京": "bj", "上海": "sh", "广州": "gz", "深圳": "sz",
        "成都": "cd", "杭州": "hz", "武汉": "wh", "南京": "nj",
        "重庆": "cq", "苏州": "su", "西安": "xa", "长沙": "cs",
        "天津": "tj", "郑州": "zz", "东莞": "dg", "青岛": "qd",
        "沈阳": "sy", "宁波": "nb", "昆明": "km", "大连": "dl",
    }

    def crawl(self, keyword: str, city: str = "全国", limit: int = 20) -> list[dict]:
        """
        爬取58同城岗位

        Args:
            keyword: 搜索关键词
            city: 城市名
            limit: 最大抓取数量

        Returns:
            标准化岗位字典列表
        """
        results = []

        # 确定城市代码
        city_code = self.CITY_CODES.get(city, "bj") if city != "全国" else "bj"

        # 拼装列表页 URL
        search_url = f"https://{city_code}.58.com/job/?key={quote(keyword)}&final=1&sort=time"
        logger.info(f"抓取列表页: {search_url}")

        html = self.fetch_page(search_url)
        if not html:
            logger.warning(f"列表页抓取失败: {search_url}")
            return results

        soup = self.parse_html(html)
        job_links = self._parse_list(soup, limit)
        logger.info(f"列表页解析到 {len(job_links)} 个岗位链接")

        for idx, (job_url, title, company_name) in enumerate(job_links):
            if idx >= limit:
                break
            try:
                detail = self._crawl_detail(job_url, keyword, city)
                if detail:
                    # 补充列表页已获取的信息
                    if not detail.get("title"):
                        detail["title"] = title
                    if not detail.get("company"):
                        detail["company"] = company_name
                    results.append(detail)
            except Exception as e:
                logger.warning(f"详情页解析失败 [{job_url}]: {e}")

        self.close()
        return results

    def _parse_list(self, soup, limit: int) -> list[tuple[str, str, str]]:
        """解析列表页，返回 [(url, title, company), ...]"""
        links = []

        # 58同城岗位列表卡片选择器（适应多个版本）
        for a_tag in soup.select("a[href*='job.shtml'], a[href*='zp/'], a.job_name, a[class*='job']"):
            href = a_tag.get("href", "").strip()
            if not href or not href.startswith("http"):
                base = "https://" + re.search(r"//([^.]+)", href or "").group(1) + ".58.com" if re.search(r"//([^.]+)", href or "") else "https://bj.58.com"
                if href.startswith("/"):
                    href = base + href
            title = a_tag.get_text(strip=True)
            if title and href and title not in ("", "全职", "兼职"):
                # 找公司名
                company = ""
                parent = a_tag.parent
                for _ in range(4):
                    if parent:
                        company_tag = parent.select_one("a[class*='comp'], span[class*='comp'], a[class*='company'], span[class*='company']")
                        if company_tag:
                            company = company_tag.get_text(strip=True)
                            break
                        parent = parent.parent

                links.append((href, title, company))
                if len(links) >= limit:
                    break

        # 去重
        seen = set()
        unique = []
        for href, title, company in links:
            key = href.split("?")[0]
            if key not in seen:
                seen.add(key)
                unique.append((href, title, company))
        return unique

    def _crawl_detail(self, url: str, keyword: str, city: str) -> dict | None:
        """抓取岗位详情页"""
        html = self.fetch_page(url)
        if not html:
            return None

        soup = self.parse_html(html)

        # 提取岗位ID
        source_id = ""
        m = re.search(r"/(\d+)x?\.shtml", url)
        if m:
            source_id = m.group(1)

        title = self.safe_extract(soup, "h1, .jobName, [class*='title']", default="")
        if not title:
            title = self.safe_extract(soup, "title", default="")
            title = re.sub(r"[-_].*", "", title).strip()

        company = self.safe_extract(
            soup, "[class*='company_name'], .compName, [class*='companyName'], a[class*='comp']",
            default="",
        )

        # 薪资
        salary_text = self.safe_extract(
            soup, "[class*='salary'], .jobSalary, [class*='pay']", default=""
        )
        salary_min, salary_max = self.normalize_salary(salary_text)

        # 位置
        location = self.safe_extract(
            soup, "[class*='location'], .jobAddr, [class*='address']", default=""
        )
        area = ""
        city_name = city
        if location:
            parts = location.split()
            if len(parts) >= 2:
                city_name = parts[0].rstrip("市")
                area = parts[1]
            elif len(parts) == 1:
                area = parts[0]

        # 经验/学历
        exp_edu = self.safe_extract_all(
            soup, "[class*='limit'], .jobLimit, [class*='condition'] span, .job_condition span"
        )
        experience = ""
        education = ""
        for item in exp_edu:
            if re.search(r"经验|应届|年", item):
                experience = item
            elif re.search(r"学历|本科|硕士|博士|大专", item):
                education = item

        # 职位描述
        desc = self.safe_extract(
            soup, "[class*='des'], .jobDes, [class*='intro'], .job_intro", default=""
        )
        if not desc:
            desc = self.safe_extract(soup, ".posDesc, .job_detail, main", default="")

        # 技能
        full_text = f"{title} {desc} {company}"
        skills = self.extract_skills_from_text(full_text)

        if not title and not company:
            return None

        return {
            "source_id": source_id,
            "source": self.SOURCE,
            "source_name": self.SOURCE_NAME,
            "source_url": url.split("?")[0],
            "title": title.strip()[:200],
            "company": company.strip()[:200] if company else "",
            "company_logo": None,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "city": city_name,
            "area": area,
            "experience_required": experience,
            "education_required": education,
            "skills": skills,
            "description": (desc.strip()[:5000] if desc else None),
            "is_active": True,
            "crawl_time": datetime.now(timezone.utc),
        }
