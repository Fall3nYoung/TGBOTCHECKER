import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.config import load_config
from bot.handlers import router
from bot.scheduler import setup_scheduler
from bot.storage import init_db


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config = load_config()

    await init_db()

    bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(router)

    scheduler = setup_scheduler(bot, config)
    scheduler.start()

    await dp.start_polling(bot, config=config)


if __name__ == "__main__":
    asyncio.run(main())
