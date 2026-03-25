"""Zentrale Konfiguration - liest aus config/settings.yaml + .env."""

from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_PATH = PROJECT_ROOT / "data"
CONFIG_PATH = PROJECT_ROOT / "config"


class DatabaseSettings(BaseSettings):
    url: str = "postgresql://ngdai:ngdai@localhost:5432/ngdai"
    echo: bool = False
    graph_name: str = "ngdai_graph"


class RedisSettings(BaseSettings):
    url: str = "redis://localhost:6379/0"


class LLMSettings(BaseSettings):
    provider: str = "anthropic"
    extraction_model: str = "claude-sonnet-4-20250514"
    reasoning_model: str = "claude-opus-4-20250514"
    api_key: str = ""
    temperature: float = 0.0
    max_retries: int = 3


class ExtractionSettings(BaseSettings):
    double_extraction: bool = True
    confidence_threshold: float = 0.8
    sliding_window_overlap_chars: int = 2000


class QuerySettings(BaseSettings):
    max_results: int = 50
    embedding_similarity_threshold: float = 0.7
    fallback_enabled: bool = True


class Settings(BaseSettings):
    """Hauptkonfiguration fuer ngdai."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_prefix="NGDAI_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    env: str = "development"
    debug: bool = True
    data_path: Path = DATA_PATH

    # Sub-Configs
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    extraction: ExtractionSettings = Field(default_factory=ExtractionSettings)
    query: QuerySettings = Field(default_factory=QuerySettings)

    # Anthropic API Key (top-level convenience)
    anthropic_api_key: str = ""

    def get_llm_api_key(self) -> str:
        """Liefert den API Key - aus llm.api_key oder anthropic_api_key."""
        return self.llm.api_key or self.anthropic_api_key


@lru_cache()
def get_settings() -> Settings:
    """Singleton Settings-Instanz."""
    return Settings()
