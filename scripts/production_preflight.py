"""Validate deployment-critical production settings without printing secrets."""
from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import create_engine, text

from app.core.config import settings


PLACEHOLDERS = {"", "change-me-in-production", "CHANGE_ME_RANDOM_64_CHARACTERS"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-database", action="store_true")
    parser.add_argument("--prepare-directories", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    if settings.APP_ENV.lower() != "production":
        errors.append("APP_ENV 必须为 production")
    if settings.DEBUG:
        errors.append("DEBUG 必须为 False")
    if settings.AUTO_CREATE_TABLES:
        errors.append("AUTO_CREATE_TABLES 必须为 False，生产环境使用 Alembic")
    for name, value in (
        ("SECRET_KEY", settings.SECRET_KEY),
        ("JWT_SECRET_KEY", settings.JWT_SECRET_KEY),
        ("PLATFORM_STATE_ENCRYPTION_KEY", settings.PLATFORM_STATE_ENCRYPTION_KEY),
    ):
        if value in PLACEHOLDERS or value.startswith("CHANGE_ME") or len(value) < 32:
            errors.append(f"{name} 必须替换为至少32字符的随机密钥")
    if not settings.DB_PASSWORD or settings.DB_PASSWORD.startswith("CHANGE_ME"):
        errors.append("DB_PASSWORD 尚未配置")
    if not settings.TENCENT_MAAS_API_KEY or settings.TENCENT_MAAS_API_KEY.startswith("CHANGE_ME"):
        errors.append("TENCENT_MAAS_API_KEY 尚未配置")
    if "*" in settings.allowed_hosts_list:
        errors.append("ALLOWED_HOSTS 不能在生产环境使用 *")
    if any(not origin.startswith("https://") for origin in settings.cors_origins_list):
        warnings.append("CORS_ORIGINS 建议全部使用 HTTPS")
    if not settings.QDRANT_ENABLED:
        warnings.append("QDRANT_ENABLED=False，将使用本地关键词检索而不是向量检索")
    if not settings.PLAYWRIGHT_CDP_ENDPOINT.strip():
        warnings.append("未配置 PLAYWRIGHT_CDP_ENDPOINT，云服务器上无法提供可视化58手动登录")

    runtime_dirs = [
        Path(settings.UPLOAD_DIR),
        Path(settings.PLATFORM_STATE_DIR),
        Path(settings.QDRANT_LOCAL_PATH),
        Path(settings.OPERATIONS_ALERT_LOG).parent,
    ]
    if args.prepare_directories:
        for directory in runtime_dirs:
            directory.mkdir(parents=True, exist_ok=True)
    for directory in runtime_dirs:
        if not directory.exists():
            errors.append(f"运行目录不存在: {directory}")

    source_dirs = [
        settings.RESUME_OPTIMIZATION_KB_SOURCE_DIR,
        settings.CAREER_PLANNING_KB_SOURCE_DIR,
        settings.SKILL_ASSESSMENT_KB_SOURCE_DIR,
        settings.JOB_RECOMMENDATION_KB_SOURCE_DIR,
        settings.HR_COMMUNICATION_KB_SOURCE_DIR,
        settings.INTERVIEW_PYTHON_KB_SOURCE_DIR,
        settings.INTERVIEW_SECRETARY_KB_SOURCE_DIR,
    ]
    for directory in source_dirs:
        if not Path(directory).exists():
            errors.append(f"知识库源目录不存在: {directory}")

    if args.check_database and not errors:
        engine = create_engine(settings.DATABASE_URL.replace("+aiomysql", "+pymysql"))
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception:
            errors.append("数据库连接失败（详细凭据不会输出）")
        finally:
            engine.dispose()

    for item in warnings:
        print(f"WARNING: {item}")
    for item in errors:
        print(f"ERROR: {item}")
    if errors:
        print(f"Preflight failed: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"Preflight passed: {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
