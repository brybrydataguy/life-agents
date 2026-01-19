from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Global configuration settings."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Base Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    CONTEXT_DIR: Path = PROJECT_ROOT / "context"
    JOURNALS_DIR: Path = PROJECT_ROOT / "journals"
    OUTPUTS_DIR: Path = PROJECT_ROOT / "outputs"

    # API Keys (loaded from .env)
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    ALPHA_VANTAGE_API_KEY: str | None = None
    POLYGON_IO_API_KEY: str | None = None
    FMP_API_KEY: str | None = None
    FRED_API_KEY: str | None = None

settings = Settings()
