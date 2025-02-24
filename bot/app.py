# bot/app.py
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers.start import router as start_router
from config import API_TOKEN
from bot.handlers.find_user import router as find_router
from bot.handlers.delete_user import router as delete_router
from bot.handlers.whohave import router as who_router

# Инициализация бота
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Используем MemoryStorage для хранения состояний
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрация
dp.include_router(start_router)
dp.include_router(find_router)
dp.include_router(who_router)
dp.include_router(delete_router)


# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
