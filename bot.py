from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from config import config


bot = Bot(token=config.BOT_TOKEN)
storage = RedisStorage.from_url("redis://localhost:6379")
dp = Dispatcher(storage=storage)
