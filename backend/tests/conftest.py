from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import os

os.environ.setdefault("MEDIA_DIR", "/tmp/namotai-media")

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app

@pytest.fixture
def mock_db() -> AsyncMock:
    """Мок AsyncSession — не пишет в реальную БД."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def client(mock_db: AsyncMock) -> TestClient:
    """TestClient с подменённой get_db."""

    async def override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
