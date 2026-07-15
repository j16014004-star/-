"""
数据库连接配置 - SQLAlchemy 异步引擎
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,       # 连接前 ping 一下，防止连接失效
    pool_size=10,
    max_overflow=20,
)

# 异步 Session 工厂
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """ORM 模型基类"""
    pass


async def get_db() -> AsyncSession:
    """
    获取数据库 Session 的依赖注入函数
    用于 FastAPI 的 Depends()
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
