from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import aiosqlite

DB_PATH = Path("data.db")


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                report_date TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                deadline_key TEXT NOT NULL,
                username TEXT,
                full_name TEXT,
                PRIMARY KEY (report_date, user_id, deadline_key)
            )
            """
        )
        await _ensure_columns(db)
        await db.commit()


async def _ensure_columns(db: aiosqlite.Connection) -> None:
    cursor = await db.execute("PRAGMA table_info(reports)")
    rows = await cursor.fetchall()
    existing = {row[1] for row in rows}
    if "deadline_key" not in existing:
        await db.execute(
            "ALTER TABLE reports ADD COLUMN deadline_key TEXT NOT NULL DEFAULT ''"
        )
    if "username" not in existing:
        await db.execute("ALTER TABLE reports ADD COLUMN username TEXT")
    if "full_name" not in existing:
        await db.execute("ALTER TABLE reports ADD COLUMN full_name TEXT")

@dataclass(frozen=True)
class ReportUser:
    user_id: int
    username: str | None
    full_name: str | None


async def add_report(
    report_date: date,
    user_id: int,
    deadline_key: str,
    username: str | None,
    full_name: str | None,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO reports (
                report_date, user_id, deadline_key, username, full_name
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (report_date.isoformat(), user_id, deadline_key, username, full_name),
        )
        await db.commit()


async def get_reporters(report_date: date, deadline_key: str) -> dict[int, ReportUser]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT user_id, username, full_name
            FROM reports
            WHERE report_date = ? AND deadline_key = ?
            """,
            (report_date.isoformat(), deadline_key),
        )
        rows = await cursor.fetchall()
    return {
        row[0]: ReportUser(user_id=row[0], username=row[1], full_name=row[2])
        for row in rows
    }
