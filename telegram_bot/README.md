# Клановый Военный Бот

Telegram-бот для клановых войн, написанный на Python с использованием aiogram и SQLite.

## Запуск локально

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Запустите бота:
   ```bash
   python main.py
   ```

## Деплой на Render

1. Создайте новый Web Service на Render.
2. Подключите репозиторий с кодом бота.
3. Укажите Build Command:
   ```bash
   pip install -r requirements.txt
   ```
4. Укажите Start Command:
   ```bash
   python main.py
   ```
   *Или используйте Procfile, который уже есть в репозитории.*
5. Убедитесь, что бот имеет доступ к токену в `config.py` или через переменные окружения.
