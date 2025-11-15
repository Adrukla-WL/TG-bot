"""Daily analytics report generator for Viva WaterLand Assistant."""
from __future__ import annotations

import json
import os
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from telegram import Bot

from utils.email_sender import send_email
from utils.google_sheets import update_sheet

BASE_DIR = Path(__file__).resolve().parents[1]
LOGS_DIR = BASE_DIR / "logs"
INTERACTIONS_LOG = LOGS_DIR / "interactions.log"
ANALYTICS_LOG = LOGS_DIR / "analytics.log"

LOGGER = logging.getLogger(__name__)


def _read_json_lines(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def generate_daily_report() -> Dict[str, Any]:
    interactions = _read_json_lines(INTERACTIONS_LOG)
    analytics = _read_json_lines(ANALYTICS_LOG)

    total_messages = len(interactions)
    user_messages = [entry for entry in interactions if entry.get("role") == "user"]
    assistant_messages = [entry for entry in interactions if entry.get("role") == "assistant"]

    questions = Counter(entry.get("message") for entry in user_messages)
    intents = Counter(entry.get("intent") for entry in analytics if entry.get("intent"))
    branches = Counter(entry.get("branch") for entry in analytics if entry.get("branch"))

    report = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "total_dialogs": len({entry.get("user_id") for entry in user_messages}),
        "total_messages": total_messages,
        "top_questions": questions.most_common(5),
        "branches": branches.most_common(5),
        "intents": intents.most_common(5),
        "assistant_replies": len(assistant_messages),
    }

    return report


def format_report(report: Dict[str, Any]) -> str:
    parts = [
        f"Ежедневный отчёт Viva WaterLand Assistant — {report['date']}",
        f"Всего диалогов: {report['total_dialogs']}",
        f"Всего сообщений: {report['total_messages']}",
        f"Ответов ассистента: {report['assistant_replies']}",
        "Топ вопросов:",
    ]
    for question, count in report["top_questions"]:
        parts.append(f" • {question} — {count}")

    parts.append("Популярные ветки:")
    for branch, count in report["branches"]:
        parts.append(f" • {branch} — {count}")

    parts.append("Популярные намерения:")
    for intent, count in report["intents"]:
        parts.append(f" • {intent} — {count}")

    return "\n".join(parts)


def send_daily_report() -> None:
    report = generate_daily_report()
    body = format_report(report)

    send_email("Ежедневный отчёт Viva WaterLand Assistant", body)

    spreadsheet_id = os.getenv("REPORT_SPREADSHEET_ID")
    spreadsheet_range = os.getenv("REPORT_SPREADSHEET_RANGE", "Лист1!A1")
    if spreadsheet_id:
        update_sheet(
            spreadsheet_id,
            spreadsheet_range,
            [
                [
                    report["date"],
                    report["total_dialogs"],
                    report["total_messages"],
                    report["assistant_replies"],
                ]
            ],
        )

    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if admin_chat_id and telegram_token:
        bot = Bot(token=telegram_token)
        bot.send_message(chat_id=admin_chat_id, text=body)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    send_daily_report()
