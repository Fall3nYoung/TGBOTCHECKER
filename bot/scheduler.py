from __future__ import annotations

from aiogram import Bot
from aiogram.utils.markdown import hbold
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import Config, format_user_list
from bot.storage import get_reporters
from bot.time_utils import today_in_timezone


async def send_daily_summary(bot: Bot, config: Config) -> None:
    today = today_in_timezone(config.timezone)
    reporters = await get_reporters(today)
    required = set(config.required_user_ids)
    missing = required - reporters

    text = (
        f"{hbold('Дедлайн пройден')}\n\n"
        f"{hbold('Отчитались')}:\n{format_user_list(sorted(reporters))}\n\n"
        f"{hbold('Не отчитались')}:\n{format_user_list(sorted(missing))}"
    )
    await bot.send_message(
        chat_id=config.chat_id,
        text=text,
        message_thread_id=config.report_thread_id,
    )


def setup_scheduler(bot: Bot, config: Config) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=config.timezone)
    scheduler.add_job(
        send_daily_summary,
        trigger="cron",
        hour=config.deadline_time.hour,
        minute=config.deadline_time.minute,
        args=[bot, config],
        id="daily_summary",
        replace_existing=True,
    )
    return scheduler
