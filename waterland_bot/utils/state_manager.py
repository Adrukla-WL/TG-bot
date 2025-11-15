"""Session state persistence utilities."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parents[1] / "sessions"
BASE_DIR.mkdir(parents=True, exist_ok=True)

LOGGER = logging.getLogger(__name__)


def _session_path(user_id: int | str) -> Path:
    return BASE_DIR / f"{user_id}.json"


def load_session(user_id: int | str) -> Dict[str, Any]:
    """Load a session from disk."""
    path = _session_path(user_id)
    if not path.exists():
        return {"history": []}
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        LOGGER.exception("Failed to decode session file for %s; starting new session.", user_id)
        return {"history": []}


def save_session(user_id: int | str, state: Dict[str, Any]) -> None:
    """Persist ``state`` to disk."""
    path = _session_path(user_id)
    with path.open("w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)


def update_context_history(user_id: int | str, role: str, message: str, *, markers: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Append a message to the session history and persist it."""
    session = load_session(user_id)
    history: List[Dict[str, Any]] = session.setdefault("history", [])
    history.append(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "role": role,
            "message": message,
            "markers": markers or {},
        }
    )
    save_session(user_id, session)
    return session
