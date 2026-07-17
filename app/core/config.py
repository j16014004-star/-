"""
应用配置 - 从 .env 文件加载环境变量
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from sqlalchemy.engine import URL
from urllib.parse import quote


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # 应用
    APP_NAME: str = "AI Career Agent"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    API_PREFIX: str = "/api/v1"
    AUTO_CREATE_TABLES: bool = True
    ENABLE_API_DOCS: bool = True
    ALLOWED_HOSTS: str = "*"

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
    TOTP_ENCRYPTION_KEY: str = ""

    # AI / LLM
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.7

    # 腾讯云 MaaS / AI Agent
    TENCENT_MAAS_API_KEY: str = ''
    TENCENT_MAAS_BASE_URL: str = 'https://tokenhub.tencentmaas.com/v1'
    TENCENT_MAAS_REGION: str = 'china-mainland'
    RESUME_OPTIMIZATION_MODEL: str = 'deepseek-v4-flash'
    CAREER_PLANNING_MODEL: str = 'deepseek-v4-flash'
    HR_REPLY_PROMPT_VERSION: str = 'hr-reply-v1'
    HR_INTERVIEW_PROMPT_VERSION: str = 'hr-interview-v1'
    HR_ASSISTANT_MODEL: str = 'deepseek-v4-flash'
    HR_APPLICATION_MAX_OUTPUT_TOKENS: int = 1200
    HR_APPLICATION_PROMPT_VERSION: str = 'hr-application-v1'
    TENCENT_MAAS_CHAT_MODELS: str = (
        'deepseek-v4-flash,glm-5.1,minimax-m2.7,minimax-m2.5,glm-5,kimi-k2.5'
    )
    CAREER_QUESTION_MAX_OUTPUT_TOKENS: int = 2000
    CAREER_QUESTION_COOLDOWN_SECONDS: int = 5
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
    AI_PROMPT_VERSION: str = 'resume-opt-v4'
    RESUME_OPTIMIZATION_KB_SOURCE_DIR: str = './knowledge_base/resume_optimization/source'
    RESUME_OPTIMIZATION_KB_PROCESSED_DIR: str = './knowledge_base/resume_optimization/processed'
    CAREER_PLANNING_KB_SOURCE_DIR: str = './knowledge_base/career_planning/source'
    CAREER_PLANNING_KB_PROCESSED_DIR: str = './knowledge_base/career_planning/processed'
    SKILL_ASSESSMENT_KB_SOURCE_DIR: str = './knowledge_base/skill_assessment/source'
    SKILL_ASSESSMENT_KB_PROCESSED_DIR: str = './knowledge_base/skill_assessment/processed'
    JOB_RECOMMENDATION_KB_SOURCE_DIR: str = './knowledge_base/job_recommendation/source'
    JOB_RECOMMENDATION_KB_PROCESSED_DIR: str = './knowledge_base/job_recommendation/processed'
    HR_COMMUNICATION_KB_SOURCE_DIR: str = './knowledge_base/hr_communication/source'
    HR_COMMUNICATION_KB_PROCESSED_DIR: str = './knowledge_base/hr_communication/processed'
    INTERVIEW_PYTHON_KB_SOURCE_DIR: str = './knowledge_base/interview_python_backend/source'
    INTERVIEW_PYTHON_KB_PROCESSED_DIR: str = './knowledge_base/interview_python_backend/processed'
    INTERVIEW_SECRETARY_KB_SOURCE_DIR: str = './knowledge_base/interview_secretary_studies/source'
    INTERVIEW_SECRETARY_KB_PROCESSED_DIR: str = './knowledge_base/interview_secretary_studies/processed'
    MOCK_INTERVIEW_MODEL: str = 'deepseek-v4-flash'
    MOCK_INTERVIEW_MAX_OUTPUT_TOKENS: int = 4000
    MOCK_INTERVIEW_PROMPT_VERSION: str = 'mock-interview-v1'
    QDRANT_ENABLED: bool = False
    QDRANT_LOCAL_MODE: bool = True
    QDRANT_LOCAL_PATH: str = './vector_store/qdrant'
    QDRANT_URL: str = 'http://127.0.0.1:6333'
    QDRANT_API_KEY: str = ''
    QDRANT_RESUME_COLLECTION: str = 'resume_optimization_kb'
    QDRANT_CAREER_COLLECTION: str = 'career_planning_kb'
    QDRANT_SKILL_ASSESSMENT_COLLECTION: str = 'career_skill_assessment_kb'
    QDRANT_JOB_RECOMMENDATION_COLLECTION: str = 'job_recommendation_kb'
    QDRANT_HR_COMMUNICATION_COLLECTION: str = 'hr_communication_kb'
    QDRANT_INTERVIEW_PYTHON_COLLECTION: str = 'interview_python_backend_kb'
    QDRANT_INTERVIEW_SECRETARY_COLLECTION: str = 'interview_secretary_studies_kb'
    AI_RAG_MIN_VECTOR_SCORE: float = 0.25
    AI_RAG_CANDIDATE_MULTIPLIER: int = 3
    LOCAL_KB_EMBEDDINGS: bool = True

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
    CRAWL_INTERVAL_HOURS: int = 1
    JOB_AUTO_REFRESH_ENABLED: bool = True
    HR_MONITOR_ENABLED: bool = True
    HR_MONITOR_INTERVAL_SECONDS: int = 30
    JOB_REFRESH_CHECK_MINUTES: int = 15
    CRAWL_DELAY_SECONDS: float = 2.0
    JOB_CRAWL_MAX_QUERIES: int = 6
    JOB_CRAWL_PAGE_TIMEOUT_SECONDS: int = 20
    JOB_CRAWL_ITEM_WAIT_SECONDS: int = 5
    JOB_CRAWL_EARLY_STOP_RATIO: float = 0.75
    PLAYWRIGHT_HEADLESS: bool = False
    PLAYWRIGHT_CRAWL_HEADLESS: bool = True
    PLATFORM_LOGIN_TIMEOUT_SECONDS: int = 600
    PLATFORM_STATE_DIR: str = "./storage_states"
    PLATFORM_STATE_ENCRYPTION_KEY: str = ""
    PLAYWRIGHT_CDP_ENDPOINT: str = ""
    PLAYWRIGHT_REMOTE_VIEW_URL: str = ""
    WORKER_BACKEND: str = "subprocess"
    WORKER_TASK_TIMEOUT_SECONDS: int = 900
    WORKER_TASK_MAX_RETRIES: int = 2
    OPERATIONS_ALERT_LOG: str = "./logs/alerts/operations.jsonl"

    @property
    def DATABASE_URL(self) -> str:
        """构造安全编码的 MySQL 异步连接 URL，支持密码中的特殊字符。"""
        return URL.create(
            drivername="mysql+aiomysql",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
            query={"charset": "utf8mb4"},
        ).render_as_string(hide_password=False)

    @property
    def REDIS_URL(self) -> str:
        """构造 Redis 连接 URL"""
        if self.REDIS_PASSWORD:
            password = quote(self.REDIS_PASSWORD, safe="")
            return f"redis://:{password}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def tencent_maas_chat_model_list(self) -> list[str]:
        """按配置顺序返回去重后的文本模型故障转移链。"""
        models: list[str] = []
        seen: set[str] = set()
        for value in self.TENCENT_MAAS_CHAT_MODELS.split(','):
            model = value.strip()
            if model and model not in seen:
                seen.add(model)
                models.append(model)
        return models

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def allowed_hosts_list(self) -> List[str]:
        hosts = [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]
        return hosts or ["*"]


# 全局配置单例
settings = Settings()


