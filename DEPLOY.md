# Деплой AmirDev-бота на VPS

Пошаговая инструкция для чистого VPS (пример — Ubuntu 24.04).
Бот работает через long polling, поэтому **входящие порты, кроме SSH,
открывать не нужно**, домен и TLS не требуются.

## Что нужно

- VPS: Ubuntu 22.04 / 24.04, 1 ГБ RAM, 10 ГБ диска
- SSH-доступ
- Заполненный `.env` (токен, админ-ID) — уже готов в проекте

## 1. Первый вход и базовая настройка

```sh
ssh root@IP_СЕРВЕРА
apt update && apt upgrade -y
apt install -y ufw
ufw allow OpenSSH
ufw enable
```

## 2. Установка Docker

```sh
curl -fsSL https://get.docker.com | sh
docker compose version   # проверка
```

## 3. Перенос проекта

Вариант А — через git (рекомендуется):

```sh
apt install -y git
git clone <СЫЛКА_НА_РЕПОЗИТОРИЙ> /opt/amirdev_bot
cd /opt/amirdev_bot
```

Вариант Б — вручную с локальной машины (PowerShell):

```powershell
scp bot.py config.py db.py keyboards.py services.py texts.py requirements.txt
  Dockerfile docker-compose.yml pytest.ini root@IP:/opt/amirdev_bot/
scp .env root@IP:/opt/amirdev_bot/
```

## 4. Файл .env

Проверьте, что заполнены `BOT_TOKEN` и `ADMIN_IDS`.
Защитите файл от лишних глаз:

```sh
chmod 600 /opt/amirdev_bot/.env
```

## 5. Запуск

```sh
cd /opt/amirdev_bot
docker compose up --build -d
docker compose logs -f bot    # смотрим логи, Ctrl+C чтобы выйти
```

Найдите бота в Telegram и напишите `/start` — должен ответить.

## 6. Полезные команды ( ежедневно )

```sh
docker compose ps                # статус контейнеров
docker compose logs -f bot       # логи бота
docker compose restart bot       # перезапуск бота
docker compose up --build -d     # перезапуск после правок кода
```

## 7. Заявки в базе

```sh
docker compose exec bot python -c \
  "import sqlite3; [print(r) for r in sqlite3.connect('/app/data/amirdev_bot.db').execute('SELECT * FROM leads ORDER BY id DESC').fetchall()]"
```

## 8. Бэкап заявок

```sh
docker compose cp bot:/app/data/amirdev_bot.db ./backup_$(date +%F).sqlite3
```

Восстановление:

```sh
docker compose cp ./backup_2026-11-10.sqlite3 bot:/app/data/amirdev_bot.db
docker compose restart bot
```

Бэкап можно выполнять по cron, например каждое воскресенье:

```cron
0 4 * * 0 cd /opt/amirdev_bot && docker compose cp bot:/app/data/amirdev_bot.db /root/backup_$(date +\%F).sqlite3
```

## 9. Автозапуск после перезагрузки VPS

Docker сам стартует при загрузке системы, а политика `restart: unless-stopped`
в `docker-compose.yml` поднимает бота автоматически. Проверка:

```sh
systemctl is-enabled docker
```

## 10. Аналитика и данные

- Аналитика (events) — Docker-volume `bot_data` → файл `/app/data/analytics.log`:

```sh
docker compose exec bot tail -20 /app/data/analytics.log
```

- Копировать аналитику на локальную машину:

```sh
docker compose cp bot:/app/data/analytics.log ./analytics.log
```

- Заявки — SQLite-файл в Docker-volume `bot_data` (`/app/data/amirdev_bot.db`);
  просмотр и бэкап — разделы 7 и 8.

## 11. Обновление бота

```sh
cd /opt/amirdev_bot
git pull
docker compose up --build -d
```

Заявки и аналитика сохранятся (в Docker volumes).

## 12. Безопасность

- Не публикуйте репозиторий с `.env` / не комить его (`.gitignore` уже настроен).
- Не публикуйте репозиторий с файлом базы `data/amirdev_bot.db` (там персональные данные).
- Если токен утёк — перевыпустите через @BotFather (`/revoke`) и обновите `.env`,
  затем `docker compose up -d`.
- Репо может быть приватным но токен не должен попасть даже в приват.

## Быстрая диагностика проблем

| Симптом                          | Действие                          |
|----------------------------------|-----------------------------------|
| `docker compose logs bot` пусто  | `docker compose ps`, `up --build` |
| 401 в логах бота                 | неверный `BOT_TOKEN` в `.env`     |
| `unable to open database file`   | проверьте volume `/app/data` и права на него |
| Нет уведомлений админу           | напишите боту `/start` со своего аккаунта — Telegram не даёт ботам писать тем, кто не начал диалог |
