"""Аналитика и уведомления админу (автономный режим, без бэкенда).

Заявки уходят админу в Telegram. События аналитики пишутся в локальный
JSONL-файл, чтобы при желании их можно было выгрузить.
"""
import asyncio
import json
import logging
import re
from datetime import datetime, timezone

from aiogram import Bot

import config

log = logging.getLogger(__name__)

# Телефон: не менее 7 цифр, допускаются +, -, пробелы, скобки.
_PHONE_RE = re.compile(r"^\+?[\d\s\-\(\)]{7,}$")
# Username: @ + буквы/цифры/подчёркивание, 5–32 символа после @.
_USERNAME_RE = re.compile(r"^@[A-Za-z0-9_]{5,32}$")


def track(event: str, user_id: int, **payload) -> None:
    """Записать событие аналитики в файл.

    События по ТЗ: quiz_started, quiz_step_completed, quiz_completed, quiz_abandoned.
    Синхронная обёртка вокруг асинхронной записи, чтобы не ломать Existing вызовы.
    """
    if not config.ANALYTICS_FILE:
        return
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "user_id": user_id,
        **payload,
    }
    try:
        asyncio.get_running_loop()
        # Уже внутри event loop — пишем в отдельном потоке, не блокируя loop.
        asyncio.ensure_future(_write_analytics(record))
    except RuntimeError:
        # Вне event loop — пишем синхронно.
        _write_analytics_sync(record)


async def _write_analytics(record: dict) -> None:
    try:
        await asyncio.to_thread(_write_analytics_sync, record)
    except Exception as e:  # noqa: BLE001
        log.warning("Не удалось записать аналитику: %s", e)


def _write_analytics_sync(record: dict) -> None:
    with open(config.ANALYTICS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


async def atrack(event: str, user_id: int, **payload) -> None:
    """Асинхронная запись события аналитики (предпочтительный вариант внутри хендлеров)."""
    if not config.ANALYTICS_FILE:
        return
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "user_id": user_id,
        **payload,
    }
    try:
        await asyncio.to_thread(_write_analytics_sync, record)
    except Exception as e:  # noqa: BLE001
        log.warning("Не удалось записать аналитику: %s", e)


def is_valid_contact(contact: str) -> bool:
    """Проверка контакта: телефон или username в формате @name."""
    contact = contact.strip()
    if not contact:
        return False
    if _USERNAME_RE.match(contact):
        return True
    if _PHONE_RE.match(contact):
        return True
    return False


def _esc(text: str) -> str:
    """Экранирование для HTML-режима парсинга."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


async def notify_admins(bot: Bot, lead: dict) -> None:
    """Отправить краткий бриф всем админам."""
    username = lead.get("username")
    uname = f"@{username}" if username else "—"
    tg_id = lead.get("telegram_id", "—")
    link = f'<a href="tg://user?id={tg_id}">написать</a>' if tg_id != "—" else "—"
    text = (
        "🔔 <b>Новая заявка из квиз-бота</b>\n\n"
        f"👤 Имя: {_esc(lead.get('name') or '—')}\n"
        f"Пользователь: {uname} (id {tg_id})\n"
        f"📞 Контакт: {_esc(lead.get('phone') or lead.get('contact') or '—')}\n\n"
        f"🏢 Сфера: {_esc(lead.get('business_sphere', '—'))}\n"
        f"⚙️ Задача: {_esc(lead.get('task_type', '—'))}\n"
        f"💰 Бюджет: {_esc(lead.get('budget', '—'))}\n"
        f"⏳ Сроки: {_esc(lead.get('timeline', '—'))}\n\n"
        f"✉️ {link}"
    )
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, disable_web_page_preview=True)
        except Exception as e:  # noqa: BLE001
            log.warning("Не удалось уведомить админа %s: %s", admin_id, e)
