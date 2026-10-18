import os
from pathlib import Path

try:
    from pydantic_settings import BaseSettings
    class ConfigBase(BaseSettings):
        pass
except ImportError:
    from pydantic import BaseModel
    class ConfigBase(BaseModel):
        pass

class Settings(ConfigBase):
    PROJECT_NAME: str = "Knowledge Brain (T1)"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/v1"
    
    # Auth & Network
    KB_API_KEY: str = os.getenv("KB_API_KEY", "kb_secret_dev_key_2026")
    T1_PORT: int = int(os.getenv("T1_PORT", "8000"))
    
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "claude")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    PRIMARY_MODEL: str = os.getenv("PRIMARY_MODEL", "claude-haiku-5-5")
    COMPARISON_MODEL: str = os.getenv("COMPARISON_MODEL", "gemini-2.5-flash")
    SONNET_MODEL: str = os.getenv("SONNET_MODEL", "claude-sonnet-5-5")
    
    # Storage & Retrieval
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DB_PATH: str = os.getenv("T1_DB_PATH", str(Path(__file__).resolve().parent.parent / "task1.db"))
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", str(Path(__file__).resolve().parent.parent / "chroma_db"))
    
    # Crawler Settings
    CRAWL_DELAY_SECONDS: float = float(os.getenv("CRAWL_DELAY_SECONDS", "1.0"))
    CRAWL_MAX_CONCURRENT: int = int(os.getenv("CRAWL_MAX_CONCURRENT", "2"))
    USER_AGENT: str = "AITechConsultant-KnowledgeBot/1.0 (+https://github.com/example/ai-tech-consultant)"
    SITEMAP_URL: str = "https://support.brilliantdirectories.com/support/sitemap.xml"

settings = Settings()
