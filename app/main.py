"""
AI Career Agent - FastAPI 后端入口文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 关闭时：清理数据库资源
    await engine.dispose()


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="AI 智能求职助手平台 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
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
