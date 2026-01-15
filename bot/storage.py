from __future__ import annotations

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
                PRIMARY KEY (report_date, user_id)
            )
            """
        )
        await db.commit()


async def add_report(report_date: date, user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO reports (report_date, user_id) VALUES (?, ?)",
            (report_date.isoformat(), user_id),
        )
        await db.commit()


async def get_reporters(report_date: date) -> set[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id FROM reports WHERE report_date = ?",
            (report_date.isoformat(),),
        )
        rows = await cursor.fetchall()
    return {row[0] for row in rows}
