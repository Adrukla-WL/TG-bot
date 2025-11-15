"""Utilities for interacting with Google Sheets."""
from __future__ import annotations

import logging
import os
from typing import Iterable

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

LOGGER = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_credentials() -> Credentials | None:
    key_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if not key_file or not os.path.exists(key_file):
        LOGGER.warning("Google service account file not configured: %s", key_file)
        return None

    return Credentials.from_service_account_file(key_file, scopes=SCOPES)


def update_sheet(spreadsheet_id: str, range_name: str, values: Iterable[Iterable[str]]) -> None:
    """Push data to a Google Sheet."""
    credentials = _get_credentials()
    if credentials is None:
        LOGGER.warning("Skipping Google Sheet update because credentials are unavailable.")
        return

    try:
        service = build("sheets", "v4", credentials=credentials)
        body = {"values": [list(row) for row in values]}
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body,
        ).execute()
        LOGGER.info("Google Sheet %s updated in range %s", spreadsheet_id, range_name)
    except Exception as exc:  # pragma: no cover - network operations
        LOGGER.exception("Failed to update Google Sheet: %s", exc)
