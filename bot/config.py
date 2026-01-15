from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import time
from typing import Iterable

from dotenv import load_dotenv

load_dotenv()


def _parse_user_ids(raw: str | None) -> list[int]:
    if not raw:
        return []
    ids: list[int] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        ids.append(int(item))
    return ids


def _parse_deadline(raw: str | None) -> time:
    if not raw:
        return time(hour=18, minute=0)
    parts = raw.split(":")
    if len(parts) != 2:
        raise ValueError("DEADLINE_TIME must be in HH:MM format")
    return time(hour=int(parts[0]), minute=int(parts[1]))


@dataclass(frozen=True)
class Config:
    bot_token: str
    chat_id: int
    report_thread_id: int
    deadline_time: time
    timezone: str
    required_user_ids: list[int]


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN is required")

    chat_id_raw = os.getenv("CHAT_ID")
    if not chat_id_raw:
        raise ValueError("CHAT_ID is required")

    thread_id_raw = os.getenv("REPORT_THREAD_ID")
    if not thread_id_raw:
        raise ValueError("REPORT_THREAD_ID is required")

    deadline_time = _parse_deadline(os.getenv("DEADLINE_TIME"))
    timezone = os.getenv("TIMEZONE", "Europe/Moscow")
    required_user_ids = _parse_user_ids(os.getenv("REQUIRED_USER_IDS"))

    return Config(
        bot_token=bot_token,
        chat_id=int(chat_id_raw),
        report_thread_id=int(thread_id_raw),
        deadline_time=deadline_time,
        timezone=timezone,
        required_user_ids=required_user_ids,
    )


def format_user_list(user_ids: Iterable[int]) -> str:
    ids = list(user_ids)
    if not ids:
        return "—"
    return "\n".join(f"• <code>{user_id}</code>" for user_id in ids)
