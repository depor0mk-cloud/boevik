import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from firebase_db import init_firebase
from handlers import router
from war import war_tick_loop

logging.basicConfig(level=logging.INFO)

async def main():
    init_firebase()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    
    # Start background task for wars
    asyncio.create_task(war_tick_loop(bot))
    
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
