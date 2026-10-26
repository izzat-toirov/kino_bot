import asyncio
import logging
import sys

# Windows terminalida UTF-8 emoji xatoliklarining oldini olish
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_IDS
from database import db
from handlers.admin import router as admin_router
from handlers.user import router as user_router

# Log tizimini sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# UptimeRobot va Render uchun mini veb-server (Bot uxlamasligi uchun)
async def handle_ping(request):
    return web.Response(text="🎬 Kino Bot faol ishlab turibdi (24/7)!", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Veb-server {port}-portda ishga tushdi (Render / UptimeRobot).")
    return runner

async def main():
    # Token tekshiruvi
    if not BOT_TOKEN or "YOUR_BOT_TOKEN_HERE" in BOT_TOKEN:
        print("\n" + "="*60)
        print("XATOLIK: BOT_TOKEN ko'rsatilmagan!")
        print("Iltimos, '.env' faylini oching va @BotFather'dan olgan tokeningizni yozing.")
        print("Misol:")
        print("BOT_TOKEN=123456789:ABCDefGhIJKlmNoPQRstuVWxyz")
        print("="*60 + "\n")
        return

    logger.info("Ma'lumotlar bazasi ishga tushirilmoqda...")
    await db.init_db()

    # Bot va Dispatcher yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Routerlarni ulash (Admin router birinchi bo'lishi shart!)
    dp.include_router(admin_router)
    dp.include_router(user_router)

    # Bot ma'lumotlarini olish
    bot_info = await bot.get_me()
    print("\n" + "="*50)
    print(f"[+] KINO BOT ISHGA TUSHDI!")
    print(f"[*] Bot Username: @{bot_info.username}")
    print(f"[*] Admin ID lar: {ADMIN_IDS}")
    print("="*50 + "\n")

    # Eski kutilayotgan xabarlarni tozalash (Bot qotib qolmasligi uchun)
    await bot.delete_webhook(drop_pending_updates=True)

    # UptimeRobot uchun veb-serverni fonda ishga tushirish
    web_runner = await start_web_server()

    # Pollingni boshlash
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await web_runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
