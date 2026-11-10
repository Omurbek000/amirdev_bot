"""База заявок на SQLite.

Файл базы лежит в каталоге DATA_DIR (на Bothost это /app/data), поэтому
заявки переживают перезапуск и обновление бота.
"""
import logging
import os

import aiosqlite

import config

log = logging.getLogger(__name__)

_db: aiosqlite.Connection | None = None


async def connect() -> None:
    """Открыть базу и убедиться, что таблица заявок существует."""
    global _db
    os.makedirs(config.DATA_DIR, exist_ok=True)
    _db = await aiosqlite.connect(config.DB_FILE)
    # WAL повышает надёжность записи при внезапной остановке бота.
    await _db.execute("PRAGMA journal_mode=WAL")
    await _db.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            username TEXT,
            name TEXT,
            contact TEXT NOT NULL,
            business_sphere TEXT NOT NULL,
            task_type TEXT NOT NULL,
            budget TEXT NOT NULL,
            timeline TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    await _db.commit()
    log.info("База заявок открыта: %s", config.DB_FILE)


async def save_lead(lead: dict[str, int | str | None]) -> None:
    """Сохранить заявку до подтверждения её приёма пользователю."""
    if _db is None:
        raise RuntimeError("База не открыта — сначала вызовите db.connect().")

    await _db.execute(
        """
        INSERT INTO leads (
            telegram_id, username, name, contact, business_sphere,
            task_type, budget, timeline
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead["telegram_id"],
            lead["username"],
            lead["name"],
            lead["contact"],
            lead["business_sphere"],
            lead["task_type"],
            lead["budget"],
            lead["timeline"],
        ),
    )
    await _db.commit()


async def close() -> None:
    """Закрыть базу при остановке бота."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
