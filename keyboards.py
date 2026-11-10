"""Клавиатуры и варианты ответов квиза.

Варианты хранятся как списки (key, подпись). key уходит в callback_data,
подпись показывается на кнопке и сохраняется в заявке.
Чтобы изменить вопросы под другой проект — правьте списки ниже.
"""
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

START_BTN = "🚀 Рассчитать стоимость проекта"
BACK_LABEL = "⬅️ Назад"

# Варианты ответов: (key, подпись на кнопке)
SPHERE = [
    ("goods", "🛍 Товарный бизнес"),
    ("services", "💼 Услуги"),
    ("edu", "🎓 Онлайн-школа/Инфобизнес"),
    ("production", "🏭 Производство"),
    ("horeca", "🍽 HoReCa"),
    ("other", "📦 Другое"),
]

TASK = [
    ("bot", "🤖 Telegram-бота"),
    ("site", "🌐 Сайт / Лендинг"),
    ("ads", "📈 Рекламу и трафик"),
    ("complex", "🔧 Комплексную автоматизацию"),
    ("consult", "❓ Пока не знаю, нужна консультация"),
]

BUDGET = [
    ("b50", "до 50 000 ₽"),
    ("b50_150", "50 000 — 150 000 ₽"),
    ("b150_300", "150 000 — 300 000 ₽"),
    ("b300", "300 000+ ₽"),
    ("b_consult", "Нужна консультация по цене"),
]

TIMELINE = [
    ("week", "⚡ На этой неделе"),
    ("month", "📆 В этом месяце"),
    ("quarter", "🗓 В течение квартала"),
    ("later", "🔍 Пока просто изучаю варианты"),
]

# Быстрый доступ к подписи по key (для сборки брифа).
LABELS = {k: v for group in (SPHERE, TASK, BUDGET, TIMELINE) for k, v in group}


def start_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=START_BTN, callback_data="begin")]]
    )


def _options_kb(options, prefix: str, with_back: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"{prefix}:{key}")]
        for key, label in options
    ]
    if with_back:
        rows.append([InlineKeyboardButton(text=BACK_LABEL, callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def sphere_kb() -> InlineKeyboardMarkup:
    return _options_kb(SPHERE, "sphere", with_back=False)


def task_kb() -> InlineKeyboardMarkup:
    return _options_kb(TASK, "task", with_back=True)


def budget_kb() -> InlineKeyboardMarkup:
    return _options_kb(BUDGET, "budget", with_back=True)


def timeline_kb() -> InlineKeyboardMarkup:
    return _options_kb(TIMELINE, "timeline", with_back=True)


def contact_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить контакт", request_contact=True)],
            [KeyboardButton(text="✏️ Написать вручную")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
