from unittest.mock import AsyncMock, MagicMock

import db


def test_save_lead_calls_db_execute_and_commit():
    mock_conn = MagicMock()
    mock_conn.execute = AsyncMock()
    mock_conn.commit = AsyncMock()

    db._db = mock_conn
    try:
        import asyncio

        asyncio.run(
            db.save_lead(
                {
                    "telegram_id": 1,
                    "username": "user",
                    "name": "Имя",
                    "contact": "+79001234567",
                    "phone": "+79001234567",
                    "business_sphere": "usługi",
                    "task_type": "бот",
                    "budget": "до 50 000",
                    "timeline": "неделю",
                }
            )
        )
        mock_conn.execute.assert_awaited()
        args_sql = mock_conn.execute.call_args[0][0]
        assert "INSERT INTO leads" in args_sql
        mock_conn.commit.assert_awaited()
    finally:
        db._db = None
