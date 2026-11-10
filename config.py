"""Центральный конфиг бота.

Всё настраиваемое берётся из файла .env. Чтобы перенести бота на другой
проект — просто поменяйте значения в .env, код трогать не нужно.
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _int_list(raw: str) -> list[int]:
    """Парсим список id через запятую: '123,456' -> [123, 456]."""
    result = []
    for part in (raw or "").replace(" ", "").split(","):
        if part:
            try:
                result.append(int(part))
            except ValueError:
                pass
    return result


def _int(raw: str, default: int) -> int:
    """Безопасный парсинг int с дефолтом при некорректном значении."""
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


# --- Обязательные ---
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

# Куда присылать заявки (один или несколько id через запятую).
ADMIN_IDS: list[int] = _int_list(os.getenv("ADMIN_IDS", ""))

# --- Брендинг / ссылки ---
STUDIO_NAME: str = os.getenv("STUDIO_NAME", "AmirDev")
SITE_URL: str = os.getenv("SITE_URL", "https://example.com")
CONTACT_INFO: str = os.getenv(
    "CONTACT_INFO",
    "📱 Telegram: @amirdev\n📞 Телефон: +7 000 000-00-00\n🌐 Сайт: " + SITE_URL,
)

# --- Поведение ---
# Таймаут сессии в минутах (по ТЗ — 30).
SESSION_TIMEOUT_MIN: int = _int(os.getenv("SESSION_TIMEOUT_MIN", "30"), 30)

# Минимальный интервал между заявками от одного пользователя (секунды).
RATE_LIMIT_COOLDOWN_SEC: int = _int(os.getenv("RATE_LIMIT_COOLDOWN_SEC", "300"), 300)

# --- SQLite ---
# Каталог данных (на Bothost задаётся автоматически: /app/data).
DATA_DIR: str = os.getenv("DATA_DIR", "data")
# Файл с базой заявок.
DB_FILE: str = os.getenv("DB_FILE", os.path.join(DATA_DIR, "amirdev_bot.db"))

# --- FSM / хранилище состояний ---
# redis://user:pass@host:port/db или пусто — MemoryStorage.
REDIS_URL: str = os.getenv("REDIS_URL", "")

# Файл с аналитикой (JSONL). Пусто — не писать.
ANALYTICS_FILE: str = os.getenv("ANALYTICS_FILE", "analytics.log")


def validate() -> None:
    """Проверяем критичные настройки перед стартом."""
    if not BOT_TOKEN:
        raise RuntimeError(
            "Не задан BOT_TOKEN. Скопируйте .env.example в .env и вставьте токен от @BotFather."
        )
    if not ADMIN_IDS:
        raise RuntimeError(
            "Не задан ADMIN_IDS. Укажите свой Telegram ID (узнать можно у @userinfobot)."
        )

