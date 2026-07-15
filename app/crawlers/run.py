"""
爬虫运行入口 - 支持命令行直接调用
"""
import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.crawlers.job_58 import Job58Crawler
from app.crud.job import bulk_save_jobs

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def crawl_jobs(
    keyword: str = "Python",
    city: str = "北京",
    limit: int = 20,
) -> int:
    """
    运行爬虫任务

    Args:
        keyword: 搜索关键词
        city: 城市
        limit: 最大抓取数量

    Returns:
        新增/更新的岗位数量
    """
    logger.info(f"开始抓取: keyword={keyword}, city={city}, limit={limit}")

    crawler = Job58Crawler()
    try:
        jobs_data = crawler.crawl(keyword=keyword, city=city, limit=limit)
    finally:
        crawler.close()

    if not jobs_data:
        logger.warning("未抓取到任何岗位数据")
        return 0

    logger.info(f"抓取到 {len(jobs_data)} 条岗位数据，开始入库")

    async with async_session() as db:
        async with db.begin():
            count = await bulk_save_jobs(db, jobs_data)

    logger.info(f"入库完成: {count} 条")
    return count


def cli_main():
    """命令行入口: python -m app.crawlers.run --keyword Python --city 北京 --limit 30"""
    import argparse

    parser = argparse.ArgumentParser(description="岗位爬虫")
    parser.add_argument("--keyword", default="Python", help="搜索关键词")
    parser.add_argument("--city", default="北京", help="城市")
    parser.add_argument("--limit", type=int, default=20, help="最大抓取数量")
    args = parser.parse_args()

    count = asyncio.run(crawl_jobs(
        keyword=args.keyword,
        city=args.city,
        limit=args.limit,
    ))
    print(f"任务完成: 新增/更新 {count} 条岗位")


if __name__ == "__main__":
    cli_main()
