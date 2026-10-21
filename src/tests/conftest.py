import os
from pathlib import Path

import psycopg
import pytest
from dotenv import dotenv_values
from sqlalchemy.engine import make_url

# Point the app at the test database before it is imported.
_env_file = Path(__file__).resolve().parents[1] / "api" / ".env"
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or dotenv_values(_env_file).get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not set (env var or src/api/.env)")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


def _create_database_if_missing(url: str) -> None:
    u = make_url(url)
    with psycopg.connect(
        host=u.host, port=u.port or 5432, user=u.username, password=u.password,
        dbname="postgres", autocommit=True,
    ) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (u.database,)).fetchone()
        if not exists:
            conn.execute(f'CREATE DATABASE "{u.database}"')


_create_database_if_missing(TEST_DATABASE_URL)

from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, SQLModel  # noqa: E402

from app.db import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def session():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def client(session):
    with TestClient(app) as c:
        yield c
