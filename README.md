# Telegram Bot with FastAPI

Это боилерплейт приложения для создания Telegram бота с использованием FastAPI и python-telegram-bot.

## Функциональность

- Обработка команды `/start`
- Обработка текстовых сообщений
- Обработка голосовых сообщений

## Требования

- Python 3.13
- Docker и Docker Compose

## Настройка

1. Скопируйте файл `.env.example` в `.env`:
   ```bash
   cp .env.example .env
   ```

2. Отредактируйте файл `.env` и укажите:
   - `TELEGRAM_BOT_TOKEN` - токен вашего бота от @BotFather
   - `WEBHOOK_URL` - публичный URL вашего сервера

## Запуск

### Через Docker Compose

```bash
docker-compose up --build
```

### Локальный запуск для разработки

1. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # для Linux/macOS
   # или
   .\venv\Scripts\activate  # для Windows
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Запустите приложение:
   ```bash
   uvicorn app.main:app --reload
   ```

## Структура проекта

```
telegram_bot/
├── app/
│   ├── main.py          # Основной файл приложения
│   └── config.py        # Конфигурация приложения
├── .env.example         # Пример файла с переменными окружения
├── requirements.txt     # Зависимости Python
├── Dockerfile          # Конфигурация Docker
├── docker-compose.yml  # Конфигурация Docker Compose
└── README.md          # Документация
```

## Webhook

Для работы бота требуется публичный URL с SSL-сертификатом. Вы можете использовать:
- Собственный домен с SSL
- Сервисы типа ngrok для разработки
- VPS с настроенным SSL

## Разработка

Бот настроен на работу через webhook. При запуске приложения вебхук автоматически устанавливается, 
а при остановке - удаляется.