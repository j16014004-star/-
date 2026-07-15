"""
应用配置 - 从 .env 文件加载环境变量
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # 应用
    APP_NAME: str = "AI Career Agent"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    API_PREFIX: str = "/api/v1"

    # 数据库
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "ai_career_agent"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI / LLM
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.7

    # 腾讯云 MaaS / AI Agent
    TENCENT_MAAS_API_KEY: str = ''
    TENCENT_MAAS_BASE_URL: str = 'https://tokenhub.tencentmaas.com/v1'
    TENCENT_MAAS_REGION: str = 'china-mainland'
    RESUME_OPTIMIZATION_MODEL: str = 'deepseek-v4-pro'
    CAREER_PLANNING_MODEL: str = 'deepseek-v4-pro'
    TENCENT_MAAS_EMBEDDING_MODEL: str = 'kinfra-vl-embedding-2b'
    TENCENT_MAAS_EMBEDDING_DIMENSION: int = 2048
    TENCENT_MAAS_EMBEDDING_ENDPOINT: str = '/embeddings/multimodal'
    AI_TEST_MODE: bool = False
    AI_TEST_MAX_LIVE_CALLS: int = 10
    AI_TEST_MAX_TOTAL_TOKENS: int = 100000
    AI_MAX_CONCURRENT_TASKS: int = 1
    AI_REQUEST_TIMEOUT_SECONDS: int = 120
    AI_MAX_RETRIES: int = 0
    AI_MAX_OUTPUT_TOKENS: int = 8000
    AI_THINKING_ENABLED: bool = False
    AI_TEMPERATURE: float = 0.2
    AI_RAG_TOP_K: int = 2
    AI_RAG_CHUNK_SIZE: int = 800
    AI_RAG_CHUNK_OVERLAP: int = 100
    AI_EMBEDDING_BATCH_SIZE: int = 1
    AI_MAX_RESUME_CHARS: int = 12000
    AI_PROMPT_VERSION: str = 'resume-opt-v3'
    RESUME_OPTIMIZATION_KB_SOURCE_DIR: str = './knowledge_base/resume_optimization/source'
    RESUME_OPTIMIZATION_KB_PROCESSED_DIR: str = './knowledge_base/resume_optimization/processed'
    CAREER_PLANNING_KB_SOURCE_DIR: str = './knowledge_base/career_planning/source'
    CAREER_PLANNING_KB_PROCESSED_DIR: str = './knowledge_base/career_planning/processed'
    QDRANT_ENABLED: bool = False
    QDRANT_LOCAL_MODE: bool = True
    QDRANT_LOCAL_PATH: str = './vector_store/qdrant'
    QDRANT_URL: str = 'http://127.0.0.1:6333'
    QDRANT_API_KEY: str = ''
    QDRANT_RESUME_COLLECTION: str = 'resume_optimization_kb'
    QDRANT_CAREER_COLLECTION: str = 'career_planning_kb'

    # 向量数据库
    VECTOR_DB_PATH: str = "./vector_store"
    CHROMA_COLLECTION_NAME: str = "career_knowledge"

    # 文件上传
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # 邮件
    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # 爬虫配置
    CRAWL_INTERVAL_HOURS: int = 24
    CRAWL_DELAY_SECONDS: float = 2.0
    PLAYWRIGHT_HEADLESS: bool = False
    PLAYWRIGHT_CRAWL_HEADLESS: bool = True
    PLATFORM_LOGIN_TIMEOUT_SECONDS: int = 600
    PLATFORM_STATE_DIR: str = "./storage_states"

    @property
    def DATABASE_URL(self) -> str:
        """构造 MySQL 异步连接 URL"""
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def REDIS_URL(self) -> str:
        """构造 Redis 连接 URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# 全局配置单例
settings = Settings()


