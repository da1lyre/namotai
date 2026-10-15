# tests/conftest.py
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

# Импортируем твое приложение.
# Предположим, что main.py создает app и включает router из generate.py
from app.main import app


@pytest.fixture
def client():
    """Фикстура для асинхронного клиента"""
    return AsyncClient(app=app, base_url="http://test")


@pytest.fixture(autouse=True)
def mock_media_root(tmp_path):
    """
    Подменяем MEDIA_ROOT на временную директорию pytest,
    чтобы тесты не писали в /data/media и не требовали прав root.
    """
    with patch('app.services.generate.MEDIA_ROOT', tmp_path):
        yield tmp_path


@pytest.fixture(autouse=True)
def mock_db_session():
    """
    Мокаем сессию БД, чтобы тесты не зависели от реального Postgres.
    Если хочешь интеграционные тесты с реальной БД — убери эту фикстуру
    и настрой test database URL.
    """

    async def get_fake_db():
        from unittest.mock import MagicMock
        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        return session

    with patch('app.db.session.get_db', get_fake_db):
        yield
