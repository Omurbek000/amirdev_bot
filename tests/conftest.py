import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture()
def fake_db_conn(monkeypatch):
    """Подменить соединение с БД заглушкой на время теста."""
    from unittest.mock import AsyncMock, MagicMock

    conn = MagicMock()
    conn.execute = AsyncMock()
    conn.commit = AsyncMock()
    monkeypatch.setattr("db._db", conn)
    return conn
