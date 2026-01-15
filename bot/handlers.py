from __future__ import annotations

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.markdown import hbold

from bot.config import Config, format_user_list
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
    reporters = await get_reporters(today)
    required = set(config.required_user_ids)
    missing = required - reporters
    text = (
        f"{hbold('Сегодняшний статус')}:\n\n"
        f"{hbold('Отчитались')}:\n{format_user_list(sorted(reporters))}\n\n"
        f"{hbold('Не отчитались')}:\n{format_user_list(sorted(missing))}"
    )
    await message.answer(text)


@router.message()
async def capture_reports(message: types.Message, config: Config) -> None:
    if message.message_thread_id != config.report_thread_id:
        return
    if not message.from_user or message.from_user.is_bot:
        return
    await add_report(today_in_timezone(config.timezone), message.from_user.id)
