from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction

from app.core.database import AsyncSessionLocal
from app.services.task_service import TaskService
from app.services.health_service import HealthService
from app.bot.handlers.prayer_handler import show_prayer_schedule, alarm_guide_handler
from app.bot.handlers.health_handler import show_health_dashboard, add_water_handler, sleep_settings_handler
from app.bot.handlers.start import help_handler


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani navigasi tombol reply keyboard utama dan pesan santai."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # 1. Routing Tombol Menu Utama
    if text == "🕌 Jadwal Sholat":
        await show_prayer_schedule(update, context)
        return
    elif text == "💧 Catat Minum Air":
        await add_water_handler(update, context)
        return
    elif text == "🌱 Pola Hidup Sehat":
        await show_health_dashboard(update, context)
        return
    elif text == "⏰ Set Jam Tidur/Alarm":
        await sleep_settings_handler(update, context)
        return
    elif text == "📍 Ganti Kota":
        petunjuk = (
            "📍 <b>GANTI KOTA JADWAL SHOLAT</b>\n\n"
            "Ketik perintah:\n"
            "<code>/kota &lt;Nama Kota&gt;</code>\n\n"
            "Contoh:\n"
            "• <code>/kota Surabaya</code>\n"
            "• <code>/kota Jakarta</code>\n"
            "• <code>/kota Malang</code>"
        )
        await update.message.reply_text(petunjuk, parse_mode=ParseMode.HTML)
        return
    elif text == "🔔 Panduan Alarm HP":
        await alarm_guide_handler(update, context)
        return
    elif text in ["❓ Bantuan", "/help", "/bantuan"]:
        await help_handler(update, context)
        return

    # 2. Respon Pintar untuk Pesan Santai Sehari-hari
    lowered = text.lower()

    if any(k in lowered for k in ["minum", "haus", "air putih"]):
        await add_water_handler(update, context)
        return
    elif any(k in lowered for k in ["sholat", "adzan", "ashar", "maghrib", "subuh", "dzuhur", "isya"]):
        await show_prayer_schedule(update, context)
        return
    elif any(k in lowered for k in ["tidur", "ngantuk", "istirahat"]):
        await sleep_settings_handler(update, context)
        return
    elif any(k in lowered for k in ["alarm", "weker", "dering"]):
        await alarm_guide_handler(update, context)
        return

    # Default ramah
    await update.message.reply_text(
        "👋 Halo! Silakan gunakan menu di bawah untuk memeriksa <b>🕌 Jadwal Sholat</b>, "
        "mencatat <b>💧 Minum Air</b>, atau menyetel <b>⏰ Jam Tidur/Bangun Sehat</b>.",
        parse_mode=ParseMode.HTML
    )
