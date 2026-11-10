from unittest.mock import AsyncMock, MagicMock, patch

import bot


def test_can_submit_rate_limit():
    user_id = 999
    bot.LAST_SUBMIT.pop(user_id, None)
    assert bot.can_submit(user_id) is True
    bot.mark_submit(user_id)
    assert bot.can_submit(user_id) is False
    bot.LAST_SUBMIT.pop(user_id, None)


async def test_finalize_rate_limit_blocks():
    user_id = 1001
    bot.LAST_SUBMIT[user_id] = 9999999999  # far future -> blocked

    message = MagicMock()
    message.from_user.id = user_id
    message.from_user.username = "u"
    message.answer = AsyncMock()

    state = MagicMock()
    state.get_data = AsyncMock(
        return_value={
            "name": "Имя",
            "sphere": "usługi",
            "task": "бот",
            "budget": "до 50 000",
            "timeline": "неделю",
        }
    )

    with patch("bot.db.save_lead", new_callable=AsyncMock) as mock_save, patch(
        "bot.notify_admins", new_callable=AsyncMock
    ) as mock_notify:
        await bot.finalize(message, state, contact="+79001234567")

        mock_save.assert_not_awaited()
        mock_notify.assert_not_awaited()
    message.answer.assert_awaited()
    bot.LAST_SUBMIT.pop(user_id, None)
