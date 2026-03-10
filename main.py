import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database.engine import init_db
from handlers.admin import admin_router
from handlers.group import group_router
from handlers.user import user_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("Set BOT_TOKEN in .env")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(user_router)
    dp.include_router(group_router)
    dp.include_router(admin_router)

    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
