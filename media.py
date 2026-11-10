"""Брендовые GIF-анимации квиза.

При холодном старте бот один раз загружает GIF из каталога assets/ в
Telegram (превью увидит админ), получает file_id и сохраняет кэш в
DATA_DIR/media_ids.json. На Bothost каталог /app/data переживает
обновления, поэтому повторных загрузок не будет.
"""
import json
import logging
import os

from aiogram import Bot
from aiogram.types import FSInputFile, Message

import config

log = logging.getLogger(__name__)

# Ключ -> файл в каталоге assets.
ASSETS: dict[str, str] = {
    "begin": os.path.join("assets", "quiz_begin.gif"),
    "success": os.path.join("assets", "quiz_success.gif"),
}

_ids: dict[str, str] = {}


def _cache_path() -> str:
    return os.path.join(config.DATA_DIR, "media_ids.json")


def get(key: str) -> str:
    """file_id анимации или пустая строка, если анимация недоступна."""
    return _ids.get(key, "")


async def send(message: Message, key: str) -> None:
    """Отправить брендовую GIF под ключом (тихо пропустить, если нет)."""
    file_id = get(key)
    if not file_id:
        return
    try:
        await message.answer_animation(file_id)
    except Exception as e:  # noqa: BLE001
        log.warning("Не удалось отправить анимацию %s: %s", key, e)


async def init(bot: Bot, admin_id: int | None) -> None:
    """Прочитать кэш file_id; при его отсутствии — залить GIF один раз."""
    global _ids
    for key in [k for k, path in ASSETS.items() if not os.path.exists(path)]:
        log.warning("Не найден файл анимации: %s", ASSETS[key])
        ASSETS.pop(key, None)
    if not ASSETS:
        return

    if os.path.exists(_cache_path()):
        try:
            with open(_cache_path(), encoding="utf-8") as f:
                data: dict[str, str] = json.load(f)
            if all(key in data for key in ASSETS):
                _ids = {key: data[key] for key in ASSETS}
                log.info("Кэш анимаций загружен: %s", _cache_path())
                return
        except Exception as e:  # noqa: BLE001
            log.warning("Не удалось прочитать кэш анимаций: %s", e)

    if not admin_id:
        log.warning("ADMIN_IDS пуст — некуда загрузить анимации, пропускаю.")
        return

    for key, path in ASSETS.items():
        try:
            msg = await bot.send_animation(
                chat_id=admin_id, animation=FSInputFile(path)
            )
            _ids[key] = msg.animation.file_id
        except Exception as e:  # noqa: BLE001
            log.warning("Не удалось загрузить анимацию %s: %s", path, e)

    if _ids:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        try:
            with open(_cache_path(), "w", encoding="utf-8") as f:
                json.dump(_ids, f)
            log.info("Кэш анимаций сохранён: %s", _cache_path())
        except Exception as e:  # noqa: BLE001
            log.warning("Не удалось сохранить кэш анимаций: %s", e)
