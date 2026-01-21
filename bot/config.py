from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import time
from pathlib import Path
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


@dataclass(frozen=True)
class UserRef:
    user_id: int
    name: str | None = None
    username: str | None = None

    def display(self) -> str:
        if self.username:
            normalized = self.username.lstrip("@")
            return f"@{normalized}"
        return self.name or str(self.user_id)


@dataclass(frozen=True)
class Deadline:
    key: str
    tag: str
    title: str
    weekday_time: time
    weekend_time: time

    def time_for_weekday(self, is_weekend: bool) -> time:
        return self.weekend_time if is_weekend else self.weekday_time


@dataclass(frozen=True)
class ChatConfig:
    chat_id: int
    report_thread_id: int
    required_users: list[UserRef]


@dataclass(frozen=True)
class Config:
    bot_token: str
    timezone: str
    deadlines: list[Deadline]
    chats: list[ChatConfig]


def _load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_time(raw: str | None, default_value: time) -> time:
    if not raw:
        return default_value
    parts = raw.split(":")
    if len(parts) != 2:
        raise ValueError("Time must be in HH:MM format")
    return time(hour=int(parts[0]), minute=int(parts[1]))


def _load_required_users(settings: dict, fallback_ids: list[int]) -> list[UserRef]:
    users: list[UserRef] = []
    raw_users = settings.get("required_users", [])
    for raw_user in raw_users:
        users.append(
            UserRef(
                user_id=int(raw_user["id"]),
                name=raw_user.get("name"),
                username=raw_user.get("username"),
            )
        )
    if users:
        return users
    return [UserRef(user_id=user_id) for user_id in fallback_ids]


def _load_deadlines(settings: dict) -> list[Deadline]:
    deadlines: list[Deadline] = []
    raw_deadlines = settings.get("deadlines", [])
    for raw in raw_deadlines:
        deadlines.append(
            Deadline(
                key=raw["key"],
                tag=raw["tag"],
                title=raw.get("title", raw["key"]),
                weekday_time=_parse_time(raw.get("weekday_time"), time(hour=18, minute=0)),
                weekend_time=_parse_time(raw.get("weekend_time"), time(hour=18, minute=0)),
            )
        )
    if deadlines:
        return deadlines
    return [
        Deadline(
            key="daily",
            tag="#Отчет",
            title="Ежедневный отчет",
            weekday_time=time(hour=18, minute=0),
            weekend_time=time(hour=18, minute=0),
        )
    ]


def _load_chats(settings: dict, fallback_ids: list[int]) -> list[ChatConfig]:
    chats: list[ChatConfig] = []
    raw_chats = settings.get("chats", [])
    for raw_chat in raw_chats:
        chat_required = _load_required_users(
            {"required_users": raw_chat.get("required_users", [])},
            fallback_ids,
        )
        chats.append(
            ChatConfig(
                chat_id=int(raw_chat["chat_id"]),
                report_thread_id=int(raw_chat["report_thread_id"]),
                required_users=chat_required,
            )
        )
    if chats:
        return chats
    chat_id_raw = os.getenv("CHAT_ID")
    if not chat_id_raw:
        raise ValueError("CHAT_ID is required when settings.json has no chats")
    thread_id_raw = os.getenv("REPORT_THREAD_ID")
    if not thread_id_raw:
        raise ValueError("REPORT_THREAD_ID is required when settings.json has no chats")
    return [
        ChatConfig(
            chat_id=int(chat_id_raw),
            report_thread_id=int(thread_id_raw),
            required_users=_load_required_users(settings, fallback_ids),
        )
    ]


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN is required")

    timezone = os.getenv("TIMEZONE", "Europe/Moscow")
    required_user_ids = _parse_user_ids(os.getenv("REQUIRED_USER_IDS"))
    settings_path = Path(os.getenv("SETTINGS_PATH", "settings.json"))
    settings = _load_settings(settings_path)

    return Config(
        bot_token=bot_token,
        timezone=timezone,
        deadlines=_load_deadlines(settings),
        chats=_load_chats(settings, required_user_ids),
    )


def format_user_list(users: Iterable[UserRef], marker: str | None = None) -> str:
    items = list(users)
    if not items:
        return "—"
    prefix = f"{marker} " if marker else ""
    return "\n".join(
        f"• {prefix}{user.display()} (<code>{user.user_id}</code>)" for user in items
    )
