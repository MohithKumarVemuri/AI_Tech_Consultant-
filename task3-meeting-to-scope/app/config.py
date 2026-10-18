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
    PROJECT_NAME: str = "Meeting -> Scope (T3)"
    VERSION: str = "1.0.0"
    
    # Task 1 Knowledge Brain endpoint over HTTP
    KB_BASE_URL: str = os.getenv("KB_BASE_URL", "http://localhost:8000/v1")
    KB_API_KEY: str = os.getenv("KB_API_KEY", "kb_secret_dev_key_2026")
    
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "claude")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    PRIMARY_MODEL: str = os.getenv("PRIMARY_MODEL", "claude-haiku-5-5")
    
    # Financial Configuration
    DEFAULT_HOURLY_RATE: float = float(os.getenv("T3_HOURLY_RATE", "125.0"))
    DEFAULT_CURRENCY: str = os.getenv("T3_CURRENCY", "USD")
    
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

settings = Settings()
