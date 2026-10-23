from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from app.core.database import AsyncSessionLocal
from app.services.task_service import TaskService
from app.services.prayer_service import PrayerService
from app.services.health_service import DOA_SETELAH_ADZAN
from app.core.timezone import now_local, format_dt


async def show_prayer_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan jadwal sholat 5 waktu hari ini."""
    user = update.effective_user
    if not user:
        return

    async with AsyncSessionLocal() as session:
        db_user = await TaskService.get_or_create_user(session, user.id, user.username, user.full_name)
        city = db_user.city or "Surabaya"

    timings = await PrayerService.get_prayer_times(city)
    now_loc = now_local()

    teks = (
        f"🕌 <b>JADWAL SHOLAT HARI INI</b>\n"
        f"📍 Wilayah: <b>{city} & Sekitarnya</b>\n"
        f"📅 <i>{format_dt(now_loc, include_time=False)}</i>\n\n"
        f"🌅 <b>Subuh:</b> <code>{timings.get('Fajr', '-')}</code> WIB\n"
        f"☀️ <b>Terbit:</b> <code>{timings.get('Sunrise', '-')}</code> WIB\n"
        f"☀️ <b>Dzuhur:</b> <code>{timings.get('Dhuhr', '-')}</code> WIB\n"
        f"🌤️ <b>Ashar:</b> <code>{timings.get('Asr', '-')}</code> WIB\n"
        f"🌇 <b>Maghrib:</b> <code>{timings.get('Maghrib', '-')}</code> WIB\n"
        f"🌙 <b>Isya:</b> <code>{timings.get('Isha', '-')}</code> WIB\n\n"
        f"🔔 <i>Pengingat otomatis aktif: 10 menit sebelum adzan & tepat saat adzan tiba.</i>"
    )

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📍 Ganti Kota", callback_data="change_city_prompt"),
            InlineKeyboardButton("🤲 Doa Adzan", callback_data="prayer_doa")
        ],
        [
            InlineKeyboardButton("🔔 Cara Setel Alarm HP", callback_data="show_alarm_guide")
        ]
    ])

    if update.message:
        await update.message.reply_text(teks, parse_mode=ParseMode.HTML, reply_markup=kb)
    elif update.callback_query:
        await update.callback_query.edit_message_text(teks, parse_mode=ParseMode.HTML, reply_markup=kb)


async def change_city_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani perintah /kota <nama_kota>."""
    user = update.effective_user
    if not user:
        return

    args = context.args
    if not args:
        teks = (
            "📍 <b>GANTI KOTA JADWAL SHOLAT</b>\n\n"
            "Ketik perintah diikuti nama kota Anda:\n"
            "<code>/kota &lt;Nama Kota&gt;</code>\n\n"
            "Contoh:\n"
            "• <code>/kota Surabaya</code>\n"
            "• <code>/kota Jakarta</code>\n"
            "• <code>/kota Malang</code>\n"
            "• <code>/kota Sidoarjo</code>"
        )
        await update.message.reply_text(teks, parse_mode=ParseMode.HTML)
        return

    new_city = " ".join(args).strip().title()

    async with AsyncSessionLocal() as session:
        db_user = await TaskService.get_or_create_user(session, user.id, user.username, user.full_name)
        db_user.city = new_city
        await session.commit()

    # Ambil jadwal kota baru
    timings = await PrayerService.get_prayer_times(new_city)

    sukses_msg = (
        f"✅ <b>Kota Berhasil Diubah ke: {new_city}</b>\n\n"
        f"Jadwal sholat dan alarm otomatis sekarang disesuaikan untuk wilayah <b>{new_city}</b>.\n\n"
        f"🌅 Subuh: <code>{timings.get('Fajr')}</code> WIB\n"
        f"☀️ Dzuhur: <code>{timings.get('Dhuhr')}</code> WIB\n"
        f"🌤️ Ashar: <code>{timings.get('Asr')}</code> WIB\n"
        f"🌇 Maghrib: <code>{timings.get('Maghrib')}</code> WIB\n"
        f"🌙 Isya: <code>{timings.get('Isha')}</code> WIB"
    )
    await update.message.reply_text(sukses_msg, parse_mode=ParseMode.HTML)


async def alarm_guide_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Panduan menyetel alarm HP berdering keras via Telegram."""
    panduan = (
        "🔔 <b>PANDUAN MENJADIKAN BOT SEBAGAI ALARM HP</b>\n\n"
        "Agar HP Anda berdering keras seperti alarm jam weker saat bot mengirim pengingat sholat / jam tidur:\n\n"
        "<b>Cara 1: Nada Dering Khusus Chat Telegram (Paling Mudah)</b>\n"
        "1. Buka ruang chat dengan <b>@randikariefbot</b> di Telegram HP Anda.\n"
        "2. Ketuk nama bot di bagian atas untuk membuka Profil Bot.\n"
        "3. Ketuk menu <b>Notifikasi (Notifications)</b> -> pilih <b>Kustomisasi (Customize)</b>.\n"
        "4. Aktifkan opsi: <i>Notifikasi Kustom</i>.\n"
        "5. Pada bagian <b>Suara (Sound)</b>: Pilih nada dering alarm yang keras atau suara Adzan panjang.\n"
        "6. Pada bagian <b>Prioritas (Priority)</b>: Pilih <i>Maksimal (Urgent / High)</i> agar tetap berdering saat layar mati.\n\n"
        "------------------------------------\n"
        "<b>Cara 2: Alarm Jam Weker Sistem Asli (via MacroDroid di Android)</b>\n"
        "Jika ingin jam weker HP berdering dan harus dimatikan lewat tombol dismiss:\n"
        "1. Pasang aplikasi gratis <b>MacroDroid</b> dari Play Store.\n"
        "2. Tambahkan Macro Baru:\n"
        "   • <b>Trigger:</b> <i>Notifikasi Diterima -> Pilih Aplikasi Telegram -> Teks Memuat:</i> <code>#ALARM</code>\n"
        "   • <b>Action:</b> <i>Tanggal/Waktu -> Bunyikan Alarm (Set Alarm) atau Putar Suara Sirine pada Volume 100%</i>.\n"
        "3. Selesai! Setiap bot mengirim pesan `#ALARM_SHOLAT` atau `#ALARM_BANGUN`, HP Anda otomatis membunyikan alarm sistem!"
    )

    if update.message:
        await update.message.reply_text(panduan, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.message.reply_text(panduan, parse_mode=ParseMode.HTML)
        await update.callback_query.answer()
