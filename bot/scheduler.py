from __future__ import annotations

from aiogram import Bot
from aiogram.utils.markdown import hbold
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import Config, UserRef, format_user_list
from bot.storage import get_reporters
from bot.time_utils import today_in_timezone


async def send_deadline_summary(bot: Bot, config: Config, deadline_key: str) -> None:
    today = today_in_timezone(config.timezone)
    required_by_id = {user.user_id: user for user in config.required_users}
    reporters = await get_reporters(today, deadline_key)
    missing_ids = set(required_by_id) - set(reporters)
    missing_list = [required_by_id[user_id] for user_id in sorted(missing_ids)]

    deadline = next(d for d in config.deadlines if d.key == deadline_key)

    text = (
        f"{hbold('Дедлайн пройден')}: {deadline.title}\n\n"
        f"{hbold('Отчитались✅')}:\n"
        f"{format_user_list([UserRef(user_id=r.user_id, username=r.username, name=r.full_name) for r in reporters.values()])}\n\n"
        f"{hbold('Не отчитались❌')}:\n{format_user_list(missing_list)}"
    )
    await bot.send_message(
        chat_id=config.chat_id,
        text=text,
        message_thread_id=config.report_thread_id,
    )


def setup_scheduler(bot: Bot, config: Config) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=config.timezone)
    for deadline in config.deadlines:
        scheduler.add_job(
            send_deadline_summary,
            trigger="cron",
            day_of_week="mon-fri",
            hour=deadline.weekday_time.hour,
            minute=deadline.weekday_time.minute,
            args=[bot, config, deadline.key],
            id=f"{deadline.key}_weekday",
            replace_existing=True,
        )
        scheduler.add_job(
            send_deadline_summary,
            trigger="cron",
            day_of_week="sat,sun",
            hour=deadline.weekend_time.hour,
            minute=deadline.weekend_time.minute,
            args=[bot, config, deadline.key],
            id=f"{deadline.key}_weekend",
            replace_existing=True,
        )
    return scheduler
