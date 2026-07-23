from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = APP_DIR / "config"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "trusttrace"
    db_user: str = "postgres"
    db_password: str = ""
    db_echo: bool = False

    decision_thresholds_path: Path = CONFIG_DIR / "decision_thresholds.json"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_decision_config() -> dict[str, Any]:
    path = get_settings().decision_thresholds_path
    return json.loads(path.read_text(encoding="utf-8"))
