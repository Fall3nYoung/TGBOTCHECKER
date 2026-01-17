from __future__ import annotations

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.markdown import hbold

from bot.config import Config, UserRef, format_user_list
from bot.storage import add_report, get_reporters
from bot.time_utils import today_in_timezone

router = Router()


@router.message(Command("start"))
async def start(message: types.Message, config: Config) -> None:
    await message.answer(
        "Я слежу за отчетами в теме. "
        "Отправляйте отчеты в тему, а в дедлайн я покажу список."
    )


@router.message(Command("reportstatus"))
async def report_status(message: types.Message, config: Config) -> None:
    today = today_in_timezone(config.timezone)
    required_by_id = {user.user_id: user for user in config.required_users}
    parts: list[str] = [hbold("Сегодняшний статус")]

    for deadline in config.deadlines:
        reporters = await get_reporters(today, deadline.key)
        reporters_list = sorted(
            reporters.values(), key=lambda user: user.user_id
        )
        missing_ids = set(required_by_id) - set(reporters)
        missing_list = [required_by_id[user_id] for user_id in sorted(missing_ids)]

        parts.append(
            "\n".join(
                [
                    f"\n{hbold(deadline.title)} ({deadline.tag})",
                    f"{hbold('Отчитались')}:",
                    format_user_list(
                        [
                            UserRef(
                                user_id=report.user_id,
                                username=report.username,
                                name=report.full_name,
                            )
                            for report in reporters_list
                        ]
                    ),
                    f"{hbold('Не отчитались')}:",
                    format_user_list(missing_list),
                ]
            )
        )

    await message.answer("\n\n".join(parts))


@router.message()
async def capture_reports(message: types.Message, config: Config) -> None:
    if message.message_thread_id != config.report_thread_id:
        return
    if not message.from_user or message.from_user.is_bot:
        return
    text = message.text or message.caption or ""
    if not text:
        return
    matched = [deadline for deadline in config.deadlines if deadline.tag in text]
    if not matched:
        return
    full_name = message.from_user.full_name
    username = message.from_user.username
    for deadline in matched:
        await add_report(
            today_in_timezone(config.timezone),
            message.from_user.id,
            deadline.key,
            username,
            full_name,
        )
