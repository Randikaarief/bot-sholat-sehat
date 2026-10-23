import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from telegram import Update

from app.core.config import settings
from app.core.database import init_db
from app.bot.bot_app import create_bot_app
from app.services.scheduler_service import SchedulerService

# Konfigurasi logging terpusat
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("AsistenTugas")

bot_application = None
scheduler_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manajemen daur hidup aplikasi (Startup & Graceful Shutdown)."""
    global bot_application, scheduler_service

    logger.info("Memulai inisialisasi basis data...")
    await init_db()
    logger.info("Basis data berhasil diinisialisasi.")

    if settings.TELEGRAM_BOT_TOKEN:
        logger.info("Menginisialisasi Telegram Bot...")
        bot_application = create_bot_app()
        await bot_application.initialize()

        # Inisialisasi dan jalankan scheduler
        scheduler_service = SchedulerService(bot_application.bot)
        await scheduler_service.start()

        if settings.WEBHOOK_MODE and settings.WEBHOOK_URL:
            webhook_path = f"{settings.WEBHOOK_URL.rstrip('/')}/webhook"
            logger.info(f"Mengaktifkan mode Webhook pada: {webhook_path}")
            await bot_application.bot.set_webhook(url=webhook_path)
            await bot_application.start()
        else:
            logger.info("Mengaktifkan mode Polling Telegram...")
            await bot_application.start()
            if bot_application.updater:
                await bot_application.updater.start_polling(drop_pending_updates=True)
            logger.info("Bot Telegram berhasil berjalan dan siap menerima pesan!")
    else:
        logger.warning("TELEGRAM_BOT_TOKEN tidak ditemukan. Bot Telegram berjalan dalam mode siaga.")

    yield

    # Shutdown
    logger.info("Menjalankan prosedur shutdown...")
    if scheduler_service:
        await scheduler_service.stop()

    if bot_application:
        if bot_application.updater and bot_application.updater.running:
            await bot_application.updater.stop()
        if bot_application.running:
            await bot_application.stop()
        await bot_application.shutdown()

    logger.info("Aplikasi selesai dihentikan.")


# Inisialisasi FastAPI
app = FastAPI(
    title="Asisten Pribadi & Pengingat Tugas",
    description="Bot Asisten Manajemen Tugas & Sinkronisasi LMS Vinesa UNESA",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", tags=["Info"])
async def root():
    return {
        "status": "online",
        "service": "Asisten Pribadi Bot & Reminder API",
        "version": "1.0.0",
        "timezone": settings.TIMEZONE,
        "gemini_model": settings.GEMINI_MODEL,
        "bot_configured": bool(settings.TELEGRAM_BOT_TOKEN)
    }


@app.get("/health", tags=["Monitoring"])
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "scheduler_running": bool(scheduler_service and scheduler_service.is_running),
        "bot_active": bool(bot_application and bot_application.running)
    }


@app.post("/webhook", tags=["Telegram"])
async def telegram_webhook(request: Request):
    """Endpoint webhook untuk menerima update Telegram dari server produksi."""
    if not bot_application:
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    data = await request.json()
    update = Update.de_json(data, bot_application.bot)
    await bot_application.process_update(update)
    return Response(status_code=status.HTTP_200_OK)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
