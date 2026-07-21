from __future__ import annotations

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

_REQUIRED_ENV_VARS = (
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
)


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing environment variable {name}. "
            "Create a .env file in the project root."
        )
    return value.strip()


DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=_required_env("DB_USER"),
    password=_required_env("DB_PASSWORD"),
    host=_required_env("DB_HOST"),
    port=int(_required_env("DB_PORT")),
    database=_required_env("DB_NAME"),
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides one database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
