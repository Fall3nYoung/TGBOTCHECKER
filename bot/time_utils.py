from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo


def today_in_timezone(timezone: str) -> date:
    return datetime.now(ZoneInfo(timezone)).date()


def is_weekend(day: date) -> bool:
    return day.weekday() >= 5
