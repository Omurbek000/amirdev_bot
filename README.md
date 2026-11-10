# AmirDev — Telegram-бот-квиз

Квиз из 4 вопросов + контакт. Заявки приходят админу прямо в Telegram.
Заявки сохраняются в SQLite. Docker Compose запускает бота, а файл базы
хранится в Docker volume, поэтому данные переживают перезапуски.

## Что умеет

- Сбор имени и персональное приветствие
- Пошаговый квиз: сфера → задача → бюджет → сроки → контакт
- Кнопка «⬅️ Назад» — возврат на предыдущий шаг
- Сбор контакта: кнопка «Отправить контакт» или ввод вручную
- Уведомление админу с кратким брифом при каждой заявке
- Сохранение заявок в SQLite до подтверждения пользователю
- Кнопка для нового расчёта после отправки заявки
- Таймаут сессии 30 минут (настраивается)
- Аналитика событий в файл `analytics.log`:
  `quiz_started`, `quiz_step_completed`, `quiz_completed`, `quiz_abandoned`
- Команды: `/start`, `/help`, `/cases`, `/contact`

## Запуск через Docker Compose (рекомендуется)

1. Скопируйте `.env.example` в `.env` и заполните `BOT_TOKEN` и `ADMIN_IDS`.
   Для копирования в PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Запустите контейнеры:

   ```sh
   docker compose up --build -d
   ```

База данных создаётся автоматически при старте в volume `bot_data`
(`/app/data/amirdev_bot.db`).

Полезные команды:

```sh
docker compose logs -f bot     # логи бота
docker compose ps              # состояние контейнеров
docker compose down            # остановить контейнеры, сохранив заявки
```

Чтобы посмотреть заявки:

```sh
docker compose exec bot python -c "import sqlite3; [print(r) for r in sqlite3.connect('/app/data/amirdev_bot.db').execute('SELECT * FROM leads ORDER BY id DESC').fetchall()]"
```

**Не используйте `docker compose down -v`, если хотите сохранить заявки**:
эта команда удалит volume с базой данных.

### Настройки `.env`

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен от [@BotFather](https://t.me/BotFather) |
| `ADMIN_IDS` | Ваш Telegram ID от [@userinfobot](https://t.me/userinfobot). Несколько — через запятую |
| `STUDIO_NAME` | Название студии в текстах |
| `SITE_URL` | Ссылка на сайт/кейсы |
| `CONTACT_INFO` | Контакты для `/contact` |
| `SESSION_TIMEOUT_MIN` | Таймаут сессии в минутах (по умолчанию 30) |
| `ANALYTICS_FILE` | Куда писать события (пусто — не писать) |
| `DATA_DIR` | Каталог для SQLite-базы и аналитики (на Bothost — `/app/data`) |

## Перенос на другой проект

1. Создайте нового бота у @BotFather → новый `BOT_TOKEN` в `.env`.
2. Поменяйте `STUDIO_NAME`, `SITE_URL`, `CONTACT_INFO` в `.env`.
3. Если нужны другие вопросы квиза — отредактируйте списки в `keyboards.py`
   и тексты в `texts.py`. Код `bot.py` трогать не нужно.
4. Для локального запуска без Docker установите зависимости через
   `pip install -r requirements.txt` — база создастся сама в каталоге `data/`.

## Подключение к Instagram

Бот работает в Telegram. Для «подключения к Instagram» в Instagram (BIO /
сторис / директ) ставится ссылка вида `https://t.me/имя_бота`,
по которой люди переходят в бота и проходят квиз.

## Структура

```
bot.py              — логика бота, хендлеры, FSM, таймаут
config.py           — настройки из .env
db.py               — подключение к SQLite и сохранение заявок
texts.py            — все тексты
keyboards.py        — клавиатуры и варианты ответов
services.py         — аналитика + уведомления админу
media.py            — брендовые GIF-анимации (assets/), кэш file_id в data/
Dockerfile          — образ бота
docker-compose.yml  — запуск бота (данные в volume bot_data)
```
