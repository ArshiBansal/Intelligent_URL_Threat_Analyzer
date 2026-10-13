"""
Application settings loaded from environment variables.
Never hard-code credentials. All sensitive values come from .env.
"""

from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv

# Load .env from project root (one level above config/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """Central configuration object. Values are read once at import time."""

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------
    PROJECT_ROOT: Path = PROJECT_ROOT
    ARTIFACTS_DIR: Path = PROJECT_ROOT / os.getenv("MODEL_ARTIFACTS_DIR", "artifacts")
    MODELS_DIR: Path = ARTIFACTS_DIR / "models"
    PREPROCESSORS_DIR: Path = ARTIFACTS_DIR / "preprocessors"
    METADATA_DIR: Path = ARTIFACTS_DIR / "metadata"
    DATA_DIR: Path = PROJECT_ROOT / "data"
    SAMPLES_DIR: Path = DATA_DIR / "samples"
    REPORTS_DIR: Path = DATA_DIR / "reports"

    # ------------------------------------------------------------------
    # MongoDB (local / self-hosted only – NO Atlas)
    # ------------------------------------------------------------------
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "intelligent_url_threat_analyzer")

    # Collection names
    COLLECTION_SOURCE: str = os.getenv("MONGO_COLLECTION_SOURCE", "phreshphish_records")
    COLLECTION_FEATURES: str = os.getenv("MONGO_COLLECTION_FEATURES", "derived_features")
    COLLECTION_PREDICTIONS: str = os.getenv(
        "MONGO_COLLECTION_PREDICTIONS", "prediction_history"
    )
    COLLECTION_MODELS: str = os.getenv("MONGO_COLLECTION_MODELS", "model_metadata")
    COLLECTION_EVALUATION: str = os.getenv(
        "MONGO_COLLECTION_EVALUATION", "evaluation_summaries"
    )

    # ------------------------------------------------------------------
    # Application behaviour
    # ------------------------------------------------------------------
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_URL_LENGTH: int = int(os.getenv("MAX_URL_LENGTH", "2048"))
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "50"))
    MAX_PAGE_SIZE: int = 200

    # ------------------------------------------------------------------
    # Hugging Face
    # ------------------------------------------------------------------
    HF_TOKEN: str | None = os.getenv("HF_TOKEN") or None
    HF_DATASET_NAME: str = "phreshphish/phreshphish"  # exact name – never rename

    # ------------------------------------------------------------------
    # Streamlit
    # ------------------------------------------------------------------
    STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_ADDRESS: str = os.getenv("STREAMLIT_SERVER_ADDRESS", "localhost")

    # ------------------------------------------------------------------
    # Derived helpers
    # ------------------------------------------------------------------
    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() in {"development", "dev", "local"}

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in {"production", "prod"}

    def ensure_directories(self) -> None:
        """Create required directories if they do not exist."""
        for path in (
            self.ARTIFACTS_DIR,
            self.MODELS_DIR,
            self.PREPROCESSORS_DIR,
            self.METADATA_DIR,
            self.SAMPLES_DIR,
            self.REPORTS_DIR,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


# Singleton used throughout the application
settings = get_settings()