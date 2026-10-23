from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from app.core.database import AsyncSessionLocal
from app.services.task_service import TaskService
from app.services.lms_service import LMSService
from app.core.timezone import format_dt
from app.bot.keyboards.task_keyboards import get_lms_menu_keyboard


async def lms_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani menu '🎓 Vinesa LMS' atau perintah /lms."""
    user = update.effective_user
    if not user:
        return

    async with AsyncSessionLocal() as session:
        db_user = await TaskService.get_or_create_user(session, user.id, user.username, user.full_name)

    has_url = bool(db_user.lms_ical_url)
    last_sync = format_dt(db_user.last_lms_sync) if db_user.last_lms_sync else "Belum pernah"

    if has_url:
        teks = (
            "🎓 <b>INTEGRASI LMS VINESA UNESA</b>\n\n"
            "✅ <b>Status:</b> Kalender Vinesa Terhubung\n"
            f"🕒 <b>Terakhir Disinkronkan:</b> {last_sync}\n\n"
            "Bot secara otomatis memperbarui tugas dari Vinesa setiap 3 jam. "
            "Anda juga bisa menekan tombol di bawah untuk menyinkronkan data terbaru saat ini."
        )
    else:
        teks = (
            "🎓 <b>INTEGRASI LMS VINESA UNESA</b>\n\n"
            "❌ <b>Status:</b> Belum Terhubung\n\n"
            "Hubungkan bot dengan kalender <b>Vinesa UNESA</b> Anda agar semua tugas kuliah, "
            "tenggat waktu, dan kuis otomatis dicatat dan diingatkan tanpa perlu login atau memasukkan password SSO!\n\n"
            "💡 <b>Cara Cepat:</b>\n"
            "Ketik perintah:\n"
            "<code>/link_lms &lt;URL_KALENDER_VINESA&gt;</code>\n\n"
            "Klik tombol panduan di bawah jika Anda belum tahu cara mendapatkan link kalender dari Vinesa."
        )

    reply_markup = get_lms_menu_keyboard(has_url=has_url)
    if update.message:
        await update.message.reply_text(teks, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(teks, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


async def link_lms_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani perintah /link_lms <url>."""
    user = update.effective_user
    if not user:
        return

    args = context.args
    if not args:
        teks = (
            "⚠️ <b>Format Kurang Tepat!</b>\n\n"
            "Gunakan format:\n"
            "<code>/link_lms &lt;URL_KALENDER_VINESA&gt;</code>\n\n"
            "Contoh:\n"
            "<code>/link_lms https://vinesa.unesa.ac.id/calendar/export_execute.php?userid=...&authtoken=...</code>\n\n"
            "Ketik /lms untuk melihat panduan langkah demi langkah."
        )
        await update.message.reply_text(teks, parse_mode=ParseMode.HTML)
        return

    raw_url = args[0].strip()
    if not (raw_url.startswith("http://") or raw_url.startswith("https://") or raw_url.startswith("webcal://")):
        await update.message.reply_text(
            "⚠️ URL tidak valid. Pastikan diawali dengan <code>https://</code> atau <code>webcal://</code>.",
            parse_mode=ParseMode.HTML
        )
        return

    status_msg = await update.message.reply_text("⏳ <i>Menyimpan dan menyinkronkan tugas dari Vinesa UNESA...</i>", parse_mode=ParseMode.HTML)

    async with AsyncSessionLocal() as session:
        db_user = await TaskService.get_or_create_user(session, user.id, user.username, user.full_name)
        db_user.lms_ical_url = raw_url
        await session.commit()
        await session.refresh(db_user)

        # Lakukan sinkronisasi perdana secara langsung
        count, msg = await LMSService.sync_user_lms(session, db_user)

    hasil_teks = (
        f"🎉 <b>Link Kalender Vinesa Berhasil Disimpan!</b>\n\n"
        f"📊 <b>Hasil Sinkronisasi Perdana:</b>\n"
        f"• Ditemukan: <b>{count} tugas baru</b>\n"
        f"• Status: {msg}\n\n"
        f"Semua tugas kuliah aktif telah dimasukkan ke daftar tugas dan sistem pengingat. "
        f"Gunakan menu /tugas untuk memeriksa."
    )
    await status_msg.edit_text(hasil_teks, parse_mode=ParseMode.HTML, reply_markup=get_lms_menu_keyboard(has_url=True))
