import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Report Studio VIP Pro"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    JWT_SECRET: str = "ai-report-studio-vip-pro-super-secret-key-32chars-min!"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database (Default: Async SQLite for local dev, PostgreSQL for production)
    DATABASE_URL: str = "sqlite+aiosqlite:///./storage/ai_report_studio.db"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3050",
        "http://127.0.0.1:3050",
        "http://localhost:8050",
        "http://127.0.0.1:8050",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    TEMPLATE_DIR: Path = STORAGE_DIR / "templates"
    EXPORT_DIR: Path = STORAGE_DIR / "exports"
    REPORTS_DIR: Path = STORAGE_DIR / "reports"
    
    # AI Providers Configuration
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    DEFAULT_AI_PROVIDER: str = "gemini"  # gemini, openai, anthropic, ollama
    DEFAULT_AI_MODEL: str = "gemini-2.5-flash"
    
    # Search Providers Configuration
    SEARCH_PROVIDER: str = "tavily"  # tavily, brave, serpapi, duckduckgo
    TAVILY_API_KEY: str = ""
    BRAVE_SEARCH_API_KEY: str = ""
    SERPAPI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def init_storage(self):
        """Ensure all required storage directories exist."""
        for path in [self.STORAGE_DIR, self.UPLOAD_DIR, self.TEMPLATE_DIR, self.EXPORT_DIR, self.REPORTS_DIR]:
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.init_storage()
