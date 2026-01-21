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
                chat_id INTEGER NOT NULL,
                report_thread_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                PRIMARY KEY (report_date, user_id, deadline_key, chat_id, report_thread_id)
            )
            """
        )
        await _ensure_schema(db)
        await db.commit()


async def _ensure_schema(db: aiosqlite.Connection) -> None:
    cursor = await db.execute("PRAGMA table_info(reports)")
    rows = await cursor.fetchall()
    existing = {row[1] for row in rows}
    pk_cols = [row[1] for row in rows if row[5]]
    expected_pk = {"report_date", "user_id", "deadline_key", "chat_id", "report_thread_id"}
    expected_cols = {
        "report_date",
        "user_id",
        "deadline_key",
        "chat_id",
        "report_thread_id",
        "username",
        "full_name",
    }
    if expected_pk.issubset(set(pk_cols)) and expected_cols.issubset(existing):
        return
    await _migrate_reports(db, existing)


async def _migrate_reports(db: aiosqlite.Connection, existing: set[str]) -> None:
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS reports_new (
            report_date TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            deadline_key TEXT NOT NULL,
            chat_id INTEGER NOT NULL,
            report_thread_id INTEGER NOT NULL,
            username TEXT,
            full_name TEXT,
            PRIMARY KEY (report_date, user_id, deadline_key, chat_id, report_thread_id)
        )
        """
    )
    deadline_expr = "deadline_key" if "deadline_key" in existing else "''"
    chat_expr = "chat_id" if "chat_id" in existing else "0"
    thread_expr = "report_thread_id" if "report_thread_id" in existing else "0"
    username_expr = "username" if "username" in existing else "NULL"
    full_name_expr = "full_name" if "full_name" in existing else "NULL"
    await db.execute(
        f"""
        INSERT OR REPLACE INTO reports_new (
            report_date, user_id, deadline_key, chat_id, report_thread_id, username, full_name
        )
        SELECT report_date, user_id, {deadline_expr}, {chat_expr}, {thread_expr}, {username_expr}, {full_name_expr}
        FROM reports
        """
    )
    await db.execute("DROP TABLE reports")
    await db.execute("ALTER TABLE reports_new RENAME TO reports")

@dataclass(frozen=True)
class ReportUser:
    user_id: int
    username: str | None
    full_name: str | None


async def add_report(
    report_date: date,
    user_id: int,
    deadline_key: str,
    chat_id: int,
    report_thread_id: int,
    username: str | None,
    full_name: str | None,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO reports (
                report_date, user_id, deadline_key, chat_id, report_thread_id, username, full_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_date.isoformat(),
                user_id,
                deadline_key,
                chat_id,
                report_thread_id,
                username,
                full_name,
            ),
        )
        await db.commit()


async def get_reporters(
    report_date: date, deadline_key: str, chat_id: int, report_thread_id: int
) -> dict[int, ReportUser]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT user_id, username, full_name
            FROM reports
            WHERE report_date = ? AND deadline_key = ? AND chat_id = ? AND report_thread_id = ?
            """,
            (report_date.isoformat(), deadline_key, chat_id, report_thread_id),
        )
        rows = await cursor.fetchall()
    return {
        row[0]: ReportUser(user_id=row[0], username=row[1], full_name=row[2])
        for row in rows
    }
