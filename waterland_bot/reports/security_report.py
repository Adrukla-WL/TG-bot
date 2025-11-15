"""Security monitoring report for Viva WaterLand Assistant."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from utils.email_sender import send_email

BASE_DIR = Path(__file__).resolve().parents[1]
LOGS_DIR = BASE_DIR / "logs"
SECURITY_LOG = LOGS_DIR / "security.log"

LOGGER = logging.getLogger(__name__)


def _read_json_lines(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        entries = []
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                entries.append({"raw": line})
        return entries


def generate_security_report() -> Dict[str, Any]:
    entries = _read_json_lines(SECURITY_LOG)
    suspicious = [
        entry
        for entry in entries
        if (
            entry.get("event") in {"prompt_leak_attempt", "agent_security_marker"}
            or "prompt" in json.dumps(entry, ensure_ascii=False).lower()
        )
    ]

    report = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "total_security_events": len(entries),
        "suspicious_events": len(suspicious),
        "details": entries[-20:],
    }
    return report


def format_report(report: Dict[str, Any]) -> str:
    lines = [
        f"Отчёт по безопасности Viva WaterLand Assistant — {report['date']}",
        f"Всего событий: {report['total_security_events']}",
        f"Подозрительных событий: {report['suspicious_events']}",
        "Последние события:",
    ]
    for entry in report["details"]:
        lines.append(json.dumps(entry, ensure_ascii=False))
    return "\n".join(lines)


def send_security_report() -> None:
    report = generate_security_report()
    body = format_report(report)
    send_email("Ежедневный отчёт безопасности Viva WaterLand Assistant", body)

    admin_chat_id = os.getenv("SECURITY_CHAT_ID")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if admin_chat_id and telegram_token:
        from telegram import Bot  # Local import to avoid dependency in tests

        bot = Bot(token=telegram_token)
        bot.send_message(chat_id=admin_chat_id, text=body)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    send_security_report()
