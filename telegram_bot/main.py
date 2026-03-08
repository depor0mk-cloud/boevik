import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from firebase_db import init_firebase
from handlers import router
from war import war_tick_loop

logging.basicConfig(level=logging.INFO)

async def handle(request):
    return web.Response(text="Bot is running")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Web server started on port {port}")

async def main():
    init_firebase()
    
    # Start dummy web server for Render
    await start_web_server()
    
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    # Drop pending updates to avoid processing old messages on startup
    await bot.delete_webhook(drop_pending_updates=True)
    
    dp = Dispatcher()
    dp.include_router(router)
    
    # Start background task for wars
    asyncio.create_task(war_tick_loop(bot))
    
    logging.info("Bot is running...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Polling error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
