# Personal Information System

Персональна система збереження інформації. Telegram буде єдиним інтерфейсом
взаємодії, але бізнес-логіка не залежатиме від Telegram.

## Поточний етап

Бот запускається через Telegram long polling і відповідає на `/start`.
Перший користувач, який надішле власний номер, автоматично стає Super Admin.
Наступні користувачі отримують pending-заявку, а всі Super Admin отримують
кнопки для її схвалення або відмови.

## Вимоги

- Python 3.14;
- `python-telegram-bot`;
- `python-dotenv`;
- SQLite зі стандартного модуля Python.

## Конфігурація

1. Скопіюйте `.env.example` у `.env`.
2. Укажіть `TELEGRAM_BOT_TOKEN`, отриманий від `@BotFather`.
3. За потреби змініть `DATABASE_PATH`.
4. Встановіть залежності, визначені у `pyproject.toml`.
5. Запустіть застосунок із кореневої папки проєкту:

   ```bash
   PYTHONPATH=src .venv/bin/python -m personal_bot
   ```

Після запуску створюється файл SQLite та початкові таблиці, після чого бот
підключається до Telegram.

Деталі архітектури наведено в [ARCHITECTURE.md](ARCHITECTURE.md).
