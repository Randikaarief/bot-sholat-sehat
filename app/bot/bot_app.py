import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from app.core.config import settings
from app.bot.handlers.start import start_handler, help_handler
from app.bot.handlers.prayer_handler import (
    show_prayer_schedule,
    change_city_command,
    alarm_guide_handler
)
from app.bot.handlers.health_handler import (
    show_health_dashboard,
    add_water_handler,
    sleep_settings_handler,
    set_sleep_time_command,
    set_wake_time_command
)
from app.bot.handlers.message_handler import text_message_handler
from app.bot.handlers.callbacks import callback_query_handler

logger = logging.getLogger(__name__)


def create_bot_app() -> Application:
    """Menginisialisasi dan mendaftarkan semua handler Telegram Bot."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN belum disetel di .env.")

    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # 1. Perintah Dasar
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("bantuan", help_handler))

    # 2. Perintah Ibadah & Sholat
    app.add_handler(CommandHandler("jadwal", show_prayer_schedule))
    app.add_handler(CommandHandler("kota", change_city_command))
    app.add_handler(CommandHandler("alarm", alarm_guide_handler))

    # 3. Perintah Pola Hidup Sehat & Tidur
    app.add_handler(CommandHandler("sehat", show_health_dashboard))
    app.add_handler(CommandHandler("minum", add_water_handler))
    app.add_handler(CommandHandler("tidur", sleep_settings_handler))
    app.add_handler(CommandHandler("settidur", set_sleep_time_command))
    app.add_handler(CommandHandler("setbangun", set_wake_time_command))

    # 4. Handler Callback Query (Semua Tombol Inline Keyboard)
    app.add_handler(CallbackQueryHandler(callback_query_handler))

    # 5. Handler Pesan Teks (Menu Navigasi & Teks Bebas)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    return app
