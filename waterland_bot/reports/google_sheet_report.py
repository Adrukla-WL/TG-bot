"""Utility to push aggregated analytics to Google Sheets."""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Iterable

from utils.google_sheets import update_sheet

LOGGER = logging.getLogger(__name__)


def push_to_sheet(rows: Iterable[Iterable[str]]) -> None:
    spreadsheet_id = os.getenv("REPORT_SPREADSHEET_ID")
    spreadsheet_range = os.getenv("REPORT_SPREADSHEET_RANGE", "Лист1!A1")
    if not spreadsheet_id:
        LOGGER.warning("REPORT_SPREADSHEET_ID is not set; skipping sheet update.")
        return

    timestamp = datetime.utcnow().isoformat()
    data = [[timestamp, *row] for row in rows]
    update_sheet(spreadsheet_id, spreadsheet_range, data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    push_to_sheet([["Sample", "Row"]])
