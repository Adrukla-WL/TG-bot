"""Parse special agent markers embedded in LLM responses."""
from __future__ import annotations

import re
from typing import Any, Dict

_MARKER_PATTERN = re.compile(r"<AGENT:(INTENT|BRANCH|SECURITY|ERROR|RECOMMEND)=(.*?)>")


MARKER_KEYS = {
    "INTENT": "intent",
    "BRANCH": "branch",
    "SECURITY": "security",
    "ERROR": "error",
    "RECOMMEND": "recommend",
}


def extract_markers(text: str) -> Dict[str, Any]:
    """Extract agent markers from ``text``.

    Returns a dictionary with the message free from markers and a mapping of
    detected markers. Unspecified markers are omitted from the mapping.
    """
    markers: Dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        marker_type, value = match.groups()
        markers[MARKER_KEYS[marker_type]] = value.strip()
        return ""

    clean_text = _MARKER_PATTERN.sub(replace, text).strip()

    return {
        "clean_text": clean_text,
        "markers": markers,
    }
