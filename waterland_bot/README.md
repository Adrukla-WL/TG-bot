# Viva WaterLand Assistant

Viva WaterLand Assistant — Telegram-бот, который отвечает на вопросы клиентов на основе корпоративной базы знаний WaterLand. Проект сочетает Retrieval-Augmented Generation (RAG), агентскую схему подсказок и систему аналитических отчётов.

## Структура проекта

```
waterland_bot/
├── bot.py
├── rag/
│   ├── rag_retriever.py
│   ├── waterland_index_v1.faiss        # добавить самостоятельно
│   └── waterland_meta_v1.parquet       # добавить самостоятельно
├── prompts/
│   └── agent_network_prompt.txt        # добавить самостоятельно
├── sessions/                           # JSON-файлы пользовательских сессий
├── logs/
│   ├── security.log
│   ├── interactions.log
│   └── analytics.log
├── reports/
│   ├── daily_report.py
│   ├── security_report.py
│   └── google_sheet_report.py
├── utils/
│   ├── state_manager.py
│   ├── markers.py
│   ├── email_sender.py
│   └── google_sheets.py
├── requirements.txt
└── README.md
```

## Быстрый старт

1. **Создайте и активируйте виртуальное окружение.**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\\Scripts\\activate   # Windows
   ```

2. **Установите зависимости.**

   ```bash
   pip install -r requirements.txt
   ```

3. **Добавьте файлы данных.**

   Поместите подготовленные файлы `waterland_index_v1.faiss`, `waterland_meta_v1.parquet` и `agent_network_prompt.txt` по путям, указанным в структуре проекта.

4. **Настройте переменные окружения.**

   Создайте файл `.env` или экспортируйте переменные напрямую:

   | Переменная | Описание |
   | ---------- | -------- |
   | `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота |
   | `OPENAI_API_KEY` | Ключ OpenAI API |
   | `OPENAI_MODEL` | (опционально) модель OpenAI, по умолчанию `gpt-4o-mini` |
   | `ADMIN_CHAT_ID` | (опционально) чат администратора для ежедневных отчётов |
   | `SECURITY_CHAT_ID` | (опционально) чат для отчётов по безопасности |
   | `REPORT_SPREADSHEET_ID` | (опционально) ID Google Sheets для аналитики |
   | `REPORT_SPREADSHEET_RANGE` | Диапазон листа (например, `Лист1!A1`) |
   | `GOOGLE_SERVICE_ACCOUNT_FILE` | Путь к JSON-файлу сервисного аккаунта Google |
   | `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | Настройки SMTP-сервера |
   | `SMTP_USE_SSL` | Использовать SSL (по умолчанию `true`) |
   | `EMAIL_RECIPIENTS` | Список адресов для отправки отчётов через запятую |

5. **Запустите бота.**

   ```bash
   python bot.py
   ```

## Основной функционал

- **RAG-пайплайн:** поиск релевантных чанков в FAISS и формирование контекста для LLM.
- **Агентские маркеры:** автоматическое извлечение маркеров `<AGENT:...>` и обновление состояния сессий.
- **Управление сессиями:** история диалогов хранится в `sessions/{user_id}.json` и восстанавливается после перезапусков.
- **Логирование:**
  - `security.log` — попытки промт-инъекций и срабатывания маркеров безопасности.
  - `interactions.log` — все сообщения пользователей и ответы бота в формате JSON.
  - `analytics.log` — намерения и ветки для аналитики.
- **Отчётность:** ежедневные отчёты по e-mail, в Google Sheets и в Telegram-чат администратора.

## Запуск отчётности

Скрипты в папке `reports/` можно запускать отдельными cron-заданиями:

```bash
python reports/daily_report.py
python reports/security_report.py
```

## Разработка и тестирование

- Для удобства локальной разработки рекомендуется устанавливать переменные окружения через `.env` и использовать инструмент вроде `direnv` или `dotenv`.
- Логи, сессии и отчёты не удаляются автоматически; добавьте соответствующие задачи очистки при необходимости.

## Лицензия

Проект распространяется под лицензией MIT. При использовании указывайте авторство WaterLand.
