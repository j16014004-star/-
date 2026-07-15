"""
爬虫基类 - 提供通用 HTTP 请求与页面解析能力
"""
import asyncio
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup


class BaseCrawler:
    """爬虫基类"""

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    DELAY_SECONDS = 2.0  # 请求间隔
    MAX_RETRIES = 2

    def __init__(self):
        self.client = httpx.Client(
            headers={"User-Agent": self.USER_AGENT},
            timeout=15.0,
            follow_redirects=True,
        )

    def close(self):
        self.client.close()

    def fetch_page(self, url: str) -> str | None:
        """请求页面，重试 MAX_RETRIES 次"""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = self.client.get(url)
                resp.encoding = "utf-8"
                if resp.status_code == 200:
                    return resp.text
            except Exception:
                if attempt < self.MAX_RETRIES:
                    asyncio.sleep(self.DELAY_SECONDS)
        return None

    def parse_html(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    @staticmethod
    def safe_extract(soup, selector: str, attr: str | None = None,
                     default: Any = None) -> Any:
        """安全提取元素文本或属性"""
        tag = soup.select_one(selector)
        if not tag:
            return default
        if attr:
            return tag.get(attr, default)
        return tag.get_text(strip=True)

    @staticmethod
    def safe_extract_all(soup, selector: str, attr: str | None = None) -> list[Any]:
        """安全提取多个元素"""
        tags = soup.select(selector)
        if not tags:
            return []
        results = []
        for tag in tags:
            if attr:
                val = tag.get(attr)
            else:
                val = tag.get_text(strip=True)
            if val:
                results.append(val)
        return results

    @staticmethod
    def extract_skills_from_text(text: str) -> list[str]:
        """从文本中提取技能关键词"""
        keywords = [
            "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#",
            "PHP", "Ruby", "Swift", "Kotlin", "Scala",
            "FastAPI", "Flask", "Django", "Spring", "Vue", "React", "Angular",
            "MySQL", "Redis", "MongoDB", "PostgreSQL", "Elasticsearch",
            "Docker", "Kubernetes", "Git", "Linux", "Nginx",
            "Node.js", "Express", "jQuery", "HTML", "CSS",
            "SQLAlchemy", "Alembic", "Pydantic", "JWT", "OAuth",
            "RESTful", "API", "WebSocket", "Celery", "RabbitMQ", "Kafka",
            "TensorFlow", "PyTorch", "scikit-learn", "pandas", "NumPy",
            "AWS", "Azure", "GCP", "阿里云", "腾讯云",
            "Hadoop", "Spark", "Flink", "Hive",
            "Redis", "RabbitMQ", "Nginx",
            "厨师", "面点师", "西餐厨师", "中餐厨师", "服务员", "收银员", "店员", "营业员",
            "销售", "客服", "前台", "文员", "行政", "人事", "司机", "仓管", "保安", "保洁",
            "普工", "技工", "电工", "焊工", "叉车", "会计", "出纳", "财务", "运营", "设计",
            "剪辑", "摄影", "主播", "教师", "助教", "护士", "美容师", "美发师",
        ]
        text_lower = text.lower()
        found = []
        seen = set()
        for kw in keywords:
            if kw.lower() in text_lower and kw.lower() not in seen:
                seen.add(kw.lower())
                found.append(kw)
        return found

    @classmethod
    def normalize_salary(cls, text: str) -> tuple[int | None, int | None]:
        """
        标准化薪资文本为 (min, max) 元/月
        支持: "8千-1.2万" "10k-15k" "面议" "2000-3000"
        """
        if not text or "面议" in text:
            return None, None

        text = text.replace(",", "").replace("，", "").replace(" ", "")
        salary_min, salary_max = None, None

        # 匹配 "8千-1.2万" / "8k-15k" / "2000-3000"
        m = re.search(r"(\d+\.?\d*)\s*(千|k|万|w)?\s*[-~至到]\s*(\d+\.?\d*)\s*(千|k|万|w)?", text, re.IGNORECASE)
        if m:
            v1, u1, v2, u2 = m.group(1), m.group(2), m.group(3), m.group(4)
            salary_min = int(float(v1) * cls._salary_unit(u1))
            salary_max = int(float(v2) * cls._salary_unit(u2))
        else:
            # 单个数字 + 单位
            m2 = re.search(r"(\d+\.?\d*)\s*(千|k|万|w)", text, re.IGNORECASE)
            if m2:
                v = float(m2.group(1)) * cls._salary_unit(m2.group(2))
                salary_min = salary_max = int(v)

        return salary_min, salary_max

    @staticmethod
    def _salary_unit(unit: str | None) -> int:
        """薪资单位转换"""
        if unit is None:
            return 1
        unit = unit.lower()
        if unit in ("千", "k"):
            return 1000
        if unit in ("万", "w"):
            return 10000
        return 1

    @staticmethod
    def normalize_city(name: str) -> str:
        """标准化城市名，去掉'市'后缀"""
        name = name.strip()
        if name.endswith("市"):
            name = name[:-1]
        return name
