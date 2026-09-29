import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Lucen AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Storage paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    RUNTIME_DIR: Path = DATA_DIR / "runtime"
    UPLOADS_DIR: Path = RUNTIME_DIR / "uploads"
    ARTIFACTS_DIR: Path = RUNTIME_DIR / "artifacts"
    MODELS_DIR: Path = BASE_DIR / "models"
    DEMO_SAMPLES_DIR: Path = DATA_DIR / "demo_samples"
    SQLITE_PATH: Path = RUNTIME_DIR / "claimguard.db"

    # Limits
    MAX_UPLOAD_MB: int = 15
    MAX_PDF_PAGES: int = 10
    RETENTION_HOURS: int = 24
    MAX_CONCURRENT_JOBS: int = 2
    DETECTOR_TIMEOUT_S: float = 30.0

    # Risk Scoring Bands
    BAND_LOW_MAX: float = 0.35
    BAND_MED_MAX: float = 0.65

    # Models & ML
    IMAGE_MODEL_ID: str = "Ateeqq/ai-vs-human-image-detector"
    OCR_ENGINE: str = "paddle"
    MOCK_ANALYSIS: int = 0

    # LLM Settings
    LLM_ENABLED: bool = True
    LLM_PROVIDER: str = ""
    LLM_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8080,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()

# Ensure runtime directories exist
settings.RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
settings.DEMO_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
