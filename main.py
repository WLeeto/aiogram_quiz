import asyncio
from aiogram import Dispatcher
from bot import bot, dp
from app.handlers import test

import logging

logging.basicConfig(
    level=logging.DEBUG,  # или INFO для менее подробного вывода
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

def setup_routers(dp: Dispatcher):
    dp.include_router(test.router)

async def main():
    setup_routers(dp)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
