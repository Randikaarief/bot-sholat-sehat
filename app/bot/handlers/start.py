from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from app.core.database import AsyncSessionLocal
from app.services.task_service import TaskService
from app.bot.keyboards.main_menu import get_main_reply_keyboard


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani perintah /start dan pendaftaran pengguna."""
    user = update.effective_user
    if not user:
        return

    async with AsyncSessionLocal() as session:
        db_user = await TaskService.get_or_create_user(
            session=session,
            telegram_id=user.id,
            username=user.username,
            full_name=user.full_name
        )

    pesan_sambutan = (
        f"👋 <b>Halo, {user.first_name}!</b>\n\n"
        f"Selamat datang di <b>Bot Pengingat Sholat 5 Waktu & Pola Hidup Sehat</b>! 🕌🌱\n\n"
        f"Saya siap menjadi asisten harian Anda untuk menjaga waktu ibadah dan kebugaran tubuh:\n\n"
        f"🕌 <b>Pengingat Sholat 5 Waktu:</b>\n"
        f"• Peringatan wudhu 10 menit sebelum waktu sholat.\n"
        f"• Notifikasi tepat waktu saat adzan berkumandang (disertai lafadz & doa adzan).\n"
        f"• Lokasi default: <b>{db_user.city or 'Surabaya'}</b> (bisa diganti via menu /kota).\n\n"
        f"🌙 <b>Pola Tidur Sehat & Alarm Bangun:</b>\n"
        f"• Pengingat tidur malam (Pukul <b>{db_user.sleep_time} WIB</b>).\n"
        f"• Alarm bangun pagi & doa (Pukul <b>{db_user.wake_time} WIB</b>).\n\n"
        f"💧 <b>Pelacak Minum Air Putih:</b>\n"
        f"• Pengingat hidrasi berkala di siang hari.\n"
        f"• Tombol satu klik untuk mencatat target 8 gelas per hari.\n\n"
        f"🔔 <b>Alarm di HP:</b> Buka menu <b>'🔔 Panduan Alarm HP'</b> untuk menyetel nada dering weker di HP Anda!\n\n"
        f"Silakan gunakan menu tombol di bawah ini untuk memulai. 👇"
    )

    await update.message.reply_text(
        text=pesan_sambutan,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_reply_keyboard()
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani perintah /help atau menu Bantuan."""
    teks = (
        "📖 <b>PANDUAN PERINTAH ASISTEN SHOLAT & HIDUP SEHAT</b>\n\n"
        "<b>🕌 Ibadah & Jadwal Sholat:</b>\n"
        "• /jadwal - Cek jadwal sholat 5 waktu hari ini\n"
        "• /kota &lt;Nama Kota&gt; - Ganti kota jadwal sholat (contoh: <code>/kota Surabaya</code>)\n\n"
        "<b>🌙 Tidur & Bangun Sehat:</b>\n"
        "• /settidur &lt;JJ:MM&gt; - Atur jam alarm tidur malam (contoh: <code>/settidur 22:00</code>)\n"
        "• /setbangun &lt;JJ:MM&gt; - Atur jam alarm bangun pagi (contoh: <code>/setbangun 04:30</code>)\n\n"
        "<b>💧 Hidrasi & Kebugaran:</b>\n"
        "• /sehat - Buka dashboard pola hidup sehat & hidrasi\n"
        "• /minum - Catat minum air (+1 gelas)\n\n"
        "<b>🔔 Alarm HP:</b>\n"
        "• /alarm - Panduan menyetel notifikasi bot agar berdering keras seperti alarm HP"
    )
    await update.message.reply_text(
        text=teks,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_reply_keyboard()
    )
