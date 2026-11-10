"""AmirDev — Telegram-бот-квиз с сохранением заявок в SQLite.

Заявки сохраняются в базе и отправляются админам в Telegram.
Запуск: python bot.py
"""
import asyncio
import logging
import sqlite3
import time

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

import config
import db
import keyboards as kb
import media
import texts
from services import atrack, is_valid_contact, notify_admins

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("amirdev_bot")

router = Router()

# Активные сессии для контроля таймаута: user_id -> мета.
SESSIONS: dict[int, dict] = {}

# Последняя отправка заявки по пользователю (для rate limit): user_id -> timestamp.
LAST_SUBMIT: dict[int, float] = {}


class Form(StatesGroup):
    name = State()
    sphere = State()
    task = State()
    budget = State()
    timeline = State()
    contact = State()


def touch(user_id: int, chat_id: int, step: int) -> None:
    """Отметить активность пользователя (для таймаута сессии)."""
    SESSIONS[user_id] = {"chat_id": chat_id, "last_active": time.time(), "step": step}


def drop(user_id: int) -> None:
    SESSIONS.pop(user_id, None)


def can_submit(user_id: int) -> bool:
    """Rate limit: можно ли отправить заявку прямо сейчас."""
    cooldown = config.RATE_LIMIT_COOLDOWN_SEC
    last = LAST_SUBMIT.get(user_id, 0)
    return (time.time() - last) >= cooldown


def mark_submit(user_id: int) -> None:
    LAST_SUBMIT[user_id] = time.time()


# Эффекты сообщений (Bot API 7.4, работают только в личке с ботом).
EFFECT_PARTY: str = "5046509860389126442"  # 🎉 конфетти — финал заявки


async def pretend_typing(message: Message, delay: float = 0.6) -> None:
    """Показать «печатает…» паузу перед ответом, чтобы диалог выглядел живым."""
    try:
        await message.bot.send_chat_action(message.chat.id, "typing")
    except Exception:  # noqa: BLE001
        return
    await asyncio.sleep(delay)


# ----------------------------- Команды -----------------------------
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    drop(message.from_user.id)
    await state.set_state(Form.name)
    await pretend_typing(message)
    await message.answer(texts.NAME_PROMPT, reply_markup=ReplyKeyboardRemove())


@router.message(Form.name, F.text)
async def on_name(message: Message, state: FSMContext) -> None:
    name = " ".join(message.text.split())
    if not name or len(name) > 64:
        await message.answer(texts.NAME_INVALID)
        return

    await state.update_data(name=name)
    touch(message.from_user.id, message.chat.id, 0)
    await state.set_state(None)
    await pretend_typing(message, 0.5)
    await message.answer(texts.welcome(name), reply_markup=kb.start_kb())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(texts.HELP)


@router.message(Command("cases"))
async def cmd_cases(message: Message) -> None:
    await message.answer(texts.CASES, disable_web_page_preview=False)


@router.message(Command("contact"))
async def cmd_contact(message: Message) -> None:
    await message.answer(texts.CONTACT)


# ----------------------------- Квиз -----------------------------
@router.callback_query(F.data == "begin")
async def start_quiz(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Form.sphere)
    await state.update_data(step=0)
    touch(cb.from_user.id, cb.message.chat.id, 0)
    await atrack("quiz_started", cb.from_user.id)
    await media.send(cb.message, "begin")
    await cb.message.edit_text(texts.Q1, reply_markup=kb.sphere_kb())
    await cb.answer()


@router.callback_query(Form.sphere, F.data.startswith("sphere:"))
async def on_sphere(cb: CallbackQuery, state: FSMContext) -> None:
    key = cb.data.split(":", 1)[1]
    await state.update_data(sphere=kb.LABELS.get(key, key), step=1)
    await state.set_state(Form.task)
    touch(cb.from_user.id, cb.message.chat.id, 1)
    await atrack("quiz_step_completed", cb.from_user.id, step=1)
    await cb.message.edit_text(texts.Q2, reply_markup=kb.task_kb())
    await cb.answer()


@router.callback_query(Form.task, F.data.startswith("task:"))
async def on_task(cb: CallbackQuery, state: FSMContext) -> None:
    key = cb.data.split(":", 1)[1]
    await state.update_data(task=kb.LABELS.get(key, key), step=2)
    await state.set_state(Form.budget)
    touch(cb.from_user.id, cb.message.chat.id, 2)
    await atrack("quiz_step_completed", cb.from_user.id, step=2)
    await cb.message.edit_text(texts.Q3, reply_markup=kb.budget_kb())
    await cb.answer()


@router.callback_query(Form.budget, F.data.startswith("budget:"))
async def on_budget(cb: CallbackQuery, state: FSMContext) -> None:
    key = cb.data.split(":", 1)[1]
    await state.update_data(budget=kb.LABELS.get(key, key), step=3)
    await state.set_state(Form.timeline)
    touch(cb.from_user.id, cb.message.chat.id, 3)
    await atrack("quiz_step_completed", cb.from_user.id, step=3)
    await cb.message.edit_text(texts.Q4, reply_markup=kb.timeline_kb())
    await cb.answer()


@router.callback_query(Form.timeline, F.data.startswith("timeline:"))
async def on_timeline(cb: CallbackQuery, state: FSMContext) -> None:
    key = cb.data.split(":", 1)[1]
    await state.update_data(timeline=kb.LABELS.get(key, key), step=4)
    await state.set_state(Form.contact)
    touch(cb.from_user.id, cb.message.chat.id, 4)
    await atrack("quiz_step_completed", cb.from_user.id, step=4)
    await cb.message.edit_text(texts.CONTACT_PROMPT)
    await cb.message.answer("Выберите способ ниже 👇", reply_markup=kb.contact_kb())
    await cb.answer()


# ----------------------------- Кнопка "Назад" -----------------------------
@router.callback_query(F.data == "back")
async def on_back(cb: CallbackQuery, state: FSMContext) -> None:
    current = await state.get_state()
    if current == Form.task.state:
        await state.set_state(Form.sphere)
        await state.update_data(step=0)
        touch(cb.from_user.id, cb.message.chat.id, 0)
        await cb.message.edit_text(texts.Q1, reply_markup=kb.sphere_kb())
    elif current == Form.budget.state:
        await state.set_state(Form.task)
        await state.update_data(step=1)
        touch(cb.from_user.id, cb.message.chat.id, 1)
        await cb.message.edit_text(texts.Q2, reply_markup=kb.task_kb())
    elif current == Form.timeline.state:
        await state.set_state(Form.budget)
        await state.update_data(step=2)
        touch(cb.from_user.id, cb.message.chat.id, 2)
        await cb.message.edit_text(texts.Q3, reply_markup=kb.budget_kb())
    else:
        await cb.answer("Это первый шаг", show_alert=False)
        return
    await cb.answer()


# ----------------------------- Шаг 5: контакт -----------------------------
@router.message(Form.contact, F.contact)
async def contact_shared(message: Message, state: FSMContext) -> None:
    contact = message.contact.phone_number
    if not is_valid_contact(contact):
        await message.answer(texts.CONTACT_INVALID)
        return
    await finalize(message, state, contact=contact)


@router.message(Form.contact, F.text == "✏️ Написать вручную")
async def contact_manual_prompt(message: Message) -> None:
    await message.answer(texts.MANUAL_CONTACT_PROMPT, reply_markup=ReplyKeyboardRemove())


@router.message(Form.contact, F.text)
async def contact_text(message: Message, state: FSMContext) -> None:
    contact = message.text.strip()
    if not is_valid_contact(contact):
        await message.answer(texts.CONTACT_INVALID)
        return
    await finalize(message, state, contact=contact)


async def finalize(message: Message, state: FSMContext, contact: str) -> None:
    """Завершить квиз: уведомить админа и показать финал."""
    user = message.from_user

    if not can_submit(user.id):
        remaining = int(
            config.RATE_LIMIT_COOLDOWN_SEC - (time.time() - LAST_SUBMIT.get(user.id, 0))
        )
        await message.answer(texts.RATE_LIMIT_ERROR.format(seconds=max(remaining, 0)))
        return

    data = await state.get_data()
    lead = {
        "telegram_id": user.id,
        "username": user.username,
        "name": data.get("name", "—"),
        "contact": contact,
        "phone": contact,
        "business_sphere": data.get("sphere", "—"),
        "task_type": data.get("task", "—"),
        "budget": data.get("budget", "—"),
        "timeline": data.get("timeline", "—"),
    }
    try:
        await db.save_lead(lead)
    except (sqlite3.Error, OSError, TimeoutError):
        log.exception("Не удалось сохранить заявку пользователя %s", user.id)
        await message.answer(texts.SAVE_ERROR)
        return

    mark_submit(user.id)
    await notify_admins(message.bot, lead)
    await atrack(
        "quiz_completed",
        user.id,
        **{k: lead[k] for k in ("business_sphere", "task_type", "budget", "timeline")},
    )
    drop(user.id)
    await state.clear()
    await pretend_typing(message, 0.7)
    await media.send(message, "success")
    await message.answer(
        texts.final_message(
            lead["business_sphere"], lead["task_type"],
            lead["budget"], lead["timeline"],
        ),
        reply_markup=ReplyKeyboardRemove(),
        disable_web_page_preview=False,
        message_effect_id=EFFECT_PARTY,
    )
    await message.answer(texts.RESTART_PROMPT, reply_markup=kb.start_kb())


# ----------------------------- Fallback -----------------------------
@router.message()
async def fallback(message: Message, state: FSMContext) -> None:
    if await state.get_state() is None:
        await message.answer(texts.NUDGE_RESTART)


# ----------------------------- Таймаут сессии -----------------------------
async def session_watcher(bot: Bot, storage: MemoryStorage) -> None:
    """Сбрасывает неактивные сессии (таймаут по ТЗ)."""
    timeout = config.SESSION_TIMEOUT_MIN * 60
    while True:
        await asyncio.sleep(60)
        now = time.time()
        for user_id, meta in list(SESSIONS.items()):
            if now - meta["last_active"] < timeout:
                continue
            chat_id = meta["chat_id"]
            step = meta.get("step", 0)
            drop(user_id)
            await atrack("quiz_abandoned", user_id, last_step=step)
            key = StorageKey(bot_id=bot.id, chat_id=chat_id, user_id=user_id)
            try:
                await storage.set_state(key, None)
                await storage.set_data(key, {})
                await bot.send_message(chat_id, texts.SESSION_EXPIRED)
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001
                log.warning("Таймаут сессии %s: %s", user_id, e)


# ----------------------------- Запуск -----------------------------
async def main() -> None:
    config.validate()
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await media.init(bot, config.ADMIN_IDS[0] if config.ADMIN_IDS else None)
    await db.connect()

    if config.REDIS_URL:
        from aiogram.fsm.storage.redis import RedisStorage

        storage = RedisStorage.from_url(config.REDIS_URL)
    else:
        storage = MemoryStorage()

    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    asyncio.create_task(session_watcher(bot, storage))
    log.info("Бот запущен. Админы: %s", config.ADMIN_IDS)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Бот остановлен.")
