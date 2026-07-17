"""Lightweight health endpoints for Nginx and Alibaba Cloud monitoring."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db


router = APIRouter(prefix="/api/health", tags=["健康检查"])


@router.get("/live")
async def liveness() -> dict:
    return {"code": 200, "message": "ok", "data": {"status": "alive"}}


@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict:
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {
        "code": 200,
        "message": "ok",
        "data": {
            "status": "ready",
            "environment": settings.APP_ENV,
            "qdrant_enabled": settings.QDRANT_ENABLED,
            "worker_backend": settings.WORKER_BACKEND,
        },
    }
