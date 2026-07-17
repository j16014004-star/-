"""
AI Career Agent - FastAPI 后端入口文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager
import asyncio

from app.core.config import settings
from app.core.database import engine, Base
from app.routers.login_use import UseLoginRouter
from app.routers.use_register import UseRegisterRouter
from app.routers.use_userinfo import UseUserInfoRouter
from app.routers.refresh import router as refresh_router
from app.routers.logout import router as logout_router
from app.routers.resumes import router as resumes_router
from app.routers.jobs import router as jobs_router
from app.routers.job_platforms import router as job_platforms_router
from app.routers.ai_tasks import router as ai_tasks_router
from app.routers.resume_optimizations import router as resume_optimizations_router
from app.routers.resume_optimizations import saved_router as saved_resume_optimizations_router
from app.routers.career_plans import plan_router as career_plans_router
from app.routers.career_plans import profile_router as career_profiles_router
from app.routers.career_plans import execution_router as career_executions_router
from app.routers.profile import router as profile_router
from app.routers.hr import router as hr_router
from app.routers.mock_interviews import router as mock_interviews_router
from app.routers.health import router as health_router
from app.services.job_refresh_service import job_refresh_scheduler
from app.services.hr_service import hr_monitor_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 开发环境可自动建表；生产环境必须先执行 alembic upgrade head。
    if settings.AUTO_CREATE_TABLES:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    scheduler_task = None
    hr_monitor_task = None
    if settings.JOB_AUTO_REFRESH_ENABLED:
        scheduler_task = asyncio.create_task(job_refresh_scheduler())
    if settings.HR_MONITOR_ENABLED:
        hr_monitor_task = asyncio.create_task(hr_monitor_scheduler())
    yield
    for task in (scheduler_task, hr_monitor_task):
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    # 关闭时：清理数据库资源
    await engine.dispose()


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="AI 智能求职助手平台 API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_API_DOCS else None,
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# 注册路由
# ============================
# 用户注册路由
app.include_router(UseRegisterRouter)

# 用户登录路由
app.include_router(UseLoginRouter)

# 用户信息路由
app.include_router(UseUserInfoRouter)
app.include_router(profile_router)

# Token 刷新路由
app.include_router(refresh_router)

# 用户登出路由
app.include_router(logout_router)

# 简历路由
app.include_router(resumes_router)

# 岗位路由
app.include_router(jobs_router)
app.include_router(job_platforms_router)
app.include_router(ai_tasks_router)
app.include_router(resume_optimizations_router)
app.include_router(saved_resume_optimizations_router)
app.include_router(career_profiles_router)
app.include_router(career_plans_router)
app.include_router(career_executions_router)
app.include_router(hr_router)
app.include_router(mock_interviews_router)
app.include_router(health_router)

avatar_dir = Path(settings.UPLOAD_DIR) / "avatars"
avatar_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads/avatars", StaticFiles(directory=str(avatar_dir)), name="avatars")
app.mount(
    "/api/uploads/avatars",
    StaticFiles(directory=str(avatar_dir)),
    name="api_avatars",
)
