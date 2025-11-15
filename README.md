# TG-bot

Проект содержит исходный код Telegram-бота «Viva WaterLand Assistant». Основная документация и инструкции по развёртыванию находятся в каталоге [`waterland_bot/`](waterland_bot/README.md).

## Быстрый старт

```bash
cd waterland_bot
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python bot.py
```

Перед запуском не забудьте добавить файлы индекса и системный промт, а также настроить переменные окружения, описанные в [`waterland_bot/README.md`](waterland_bot/README.md).
