from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from app.core.database import AsyncSessionLocal
from app.services.task_service import TaskService
from app.services.health_service import HealthService, TIPS_HIDUP_SEHAT


def generate_progress_bar(current: int, total: int = 8) -> str:
    """Membuat progress bar visual sederhana."""
    total = max(1, total)
    filled = min(10, int((current / total) * 10))
    bar = "█" * filled + "░" * (10 - filled)
    return f"[{bar}] {current}/{total} Gelas"


def get_sleep_settings_keyboard(current_sleep: str, current_wake: str) -> InlineKeyboardMarkup:
    """Keyboard interaktif dengan tombol preset cepat untuk jam tidur dan bangun."""
    buttons = [
        # Baris 1: Pilihan Cepat Jam Tidur
        [
            InlineKeyboardButton(f"{'👉 ' if current_sleep == '21:30' else ''}🌙 21:30", callback_data="setsleep_21:30"),
            InlineKeyboardButton(f"{'👉 ' if current_sleep == '22:00' else ''}🌙 22:00", callback_data="setsleep_22:00"),
            InlineKeyboardButton(f"{'👉 ' if current_sleep == '22:30' else ''}🌙 22:30", callback_data="setsleep_22:30"),
        ],
        [
            InlineKeyboardButton(f"{'👉 ' if current_sleep == '23:00' else ''}🌙 23:00", callback_data="setsleep_23:00"),
            InlineKeyboardButton(f"{'👉 ' if current_sleep == '23:30' else ''}🌙 23:30", callback_data="setsleep_23:30"),
            InlineKeyboardButton(f"{'👉 ' if current_sleep == '00:00' else ''}🌙 00:00", callback_data="setsleep_00:00"),
        ],
        # Baris 2: Pilihan Cepat Jam Bangun
        [
            InlineKeyboardButton(f"{'👉 ' if current_wake == '04:00' else ''}☀️ 04:00", callback_data="setwake_04:00"),
            InlineKeyboardButton(f"{'👉 ' if current_wake == '04:30' else ''}☀️ 04:30", callback_data="setwake_04:30"),
            InlineKeyboardButton(f"{'👉 ' if current_wake == '05:00' else ''}☀️ 05:00", callback_data="setwake_05:00"),
            InlineKeyboardButton(f"{'👉 ' if current_wake == '05:30' else ''}☀️ 05:30", callback_data="setwake_05:30"),
        ],
        [
            InlineKeyboardButton("🌱 Kembali ke Dashboard", callback_data="open_health_dash")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


async def show_health_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan dashboard pola hidup sehat dan pelacak minum."""
    user = update.effective_user
    if not user:
        return

    async with AsyncSessionLocal() as session:
        db_user = await TaskService.get_or_create_user(session, user.id, user.username, user.full_name)
        status = await HealthService.get_health_status(session, db_user)

    progress_bar = generate_progress_bar(status["water_glasses"], status["water_target"])

    teks = (
        "🌱 <b>DASHBOARD POLA HIDUP SEHAT</b>\n\n"
        f"💧 <b>Pelacak Minum Air Putih Hari Ini:</b>\n"
        f"<code>{progress_bar} ({status['water_percent']}%)</code>\n"
        f"<i>Target harian: {status['water_target']} gelas (~2 liter)</i>\n\n"
        f"🌙 <b>Jadwal Tidur Sehat:</b> Pukul <code>{status['sleep_time']} WIB</code>\n"
        f"☀️ <b>Jadwal Bangun Pagi:</b> Pukul <code>{status['wake_time']} WIB</code>\n\n"
        "💡 <b>Tips Pola Hidup Sehat Hari Ini:</b>\n"
        f"{TIPS_HIDUP_SEHAT[0]}\n\n"
        "Gunakan tombol di bawah untuk mencatat air minum atau menyetel jam tidur Anda."
    )

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💧 Catat Minum (+1 Gelas)", callback_data="water_add_one"),
            InlineKeyboardButton("⏰ Atur Jam Tidur/Bangun", callback_data="show_sleep_settings")
        ],
        [
            InlineKeyboardButton("👀 Tips Istirahat Layar", callback_data="tip_screen"),
            InlineKeyboardButton("🥗 Tips Pola Makan", callback_data="tip_nutrition")
        ]
    ])

    if update.message:
        await update.message.reply_text(teks, parse_mode=ParseMode.HTML, reply_markup=kb)
    elif update.callback_query:
        await update.callback_query.edit_message_text(teks, parse_mode=ParseMode.HTML, reply_markup=kb)


async def add_water_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menambah 1 gelas minum air putih."""
    user = update.effective_user
    if not user:
        return

    async with AsyncSessionLocal() as session:
        db_user = await TaskService.get_or_create_user(session, user.id, user.username, user.full_name)
        count, target = await HealthService.log_water(session, db_user)

    bar = generate_progress_bar(count, target)
    percent = min(100, int((count / target) * 100))

    pesan = (
        f"🎉 <b>Mantap! +1 Gelas Air Putih Tercatat.</b>\n\n"
        f"📊 <b>Progres Hari Ini:</b>\n"
        f"<code>{bar} ({percent}%)</code>\n\n"
    )
    if count >= target:
        pesan += "🏆 <b>Target 8 Gelas Tercapai Hari Ini!</b> Tubuh Anda terhidrasi dengan sempurna. Luar biasa!"
    else:
        sisa = target - count
        pesan += f"Tinggal <b>{sisa} gelas lagi</b> untuk mencapai target sehat hari ini. Terus jaga hidrasi ya!"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💧 Tambah Lagi (+1 Gelas)", callback_data="water_add_one")],
        [InlineKeyboardButton("🌱 Buka Dashboard Sehat", callback_data="open_health_dash")]
    ])

    if update.message:
        await update.message.reply_text(pesan, parse_mode=ParseMode.HTML, reply_markup=kb)
    elif update.callback_query:
        await update.callback_query.answer("💧 +1 Gelas dicatat!")
        await update.callback_query.edit_message_text(pesan, parse_mode=ParseMode.HTML, reply_markup=kb)


async def sleep_settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan menu pengaturan jam tidur dan bangun dengan tombol ubah langsung."""
    user = update.effective_user
    if not user:
        return

    async with AsyncSessionLocal() as session:
        db_user = await TaskService.get_or_create_user(session, user.id, user.username, user.full_name)

    current_sleep = db_user.sleep_time or "23:00"
    current_wake = db_user.wake_time or "04:30"

    teks = (
        "⏰ <b>PENGATURAN JAM TIDUR & BANGUN SEHAT</b>\n\n"
        f"🌙 <b>Jam Tidur Aktif:</b> <code>{current_sleep} WIB</code>\n"
        f"☀️ <b>Jam Bangun Aktif:</b> <code>{current_wake} WIB</code>\n\n"
        "💡 <b>Ubah Langsung dengan Sekali Klik Tombol di Bawah:</b>\n"
        "• Baris pertama & kedua untuk <b>Jam Tidur Malam</b>.\n"
        "• Baris ketiga untuk <b>Jam Bangun Pagi</b>.\n\n"
        "<i>Atau jika ingin jam kustom, cukup ketik:</i>\n"
        "<code>/settidur 23:15</code> atau <code>/setbangun 05:00</code>"
    )

    kb = get_sleep_settings_keyboard(current_sleep, current_wake)

    if update.message:
        await update.message.reply_text(teks, parse_mode=ParseMode.HTML, reply_markup=kb)
    elif update.callback_query:
        await update.callback_query.edit_message_text(teks, parse_mode=ParseMode.HTML, reply_markup=kb)


async def set_sleep_time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani perintah /settidur <HH:MM>."""
    user = update.effective_user
    args = context.args
    if not args or len(args[0]) < 4 or ":" not in args[0]:
        await update.message.reply_text(
            "⚠️ Format salah. Contoh: <code>/settidur 23:00</code>",
            parse_mode=ParseMode.HTML
        )
        return

    new_time = args[0].strip()
    async with AsyncSessionLocal() as session:
        db_user = await TaskService.get_or_create_user(session, user.id, user.username, user.full_name)
        db_user.sleep_time = new_time
        await session.commit()

    await update.message.reply_text(
        f"✅ <b>Jam tidur berhasil diatur ke pukul {new_time} WIB.</b>\n"
        f"Setiap jam {new_time} malam, bot akan membunyikan audio relaksasi tidur sehat Anda.",
        parse_mode=ParseMode.HTML
    )


async def set_wake_time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani perintah /setbangun <HH:MM>."""
    user = update.effective_user
    args = context.args
    if not args or len(args[0]) < 4 or ":" not in args[0]:
        await update.message.reply_text(
            "⚠️ Format salah. Contoh: <code>/setbangun 04:30</code>",
            parse_mode=ParseMode.HTML
        )
        return

    new_time = args[0].strip()
    async with AsyncSessionLocal() as session:
        db_user = await TaskService.get_or_create_user(session, user.id, user.username, user.full_name)
        db_user.wake_time = new_time
        await session.commit()

    await update.message.reply_text(
        f"✅ <b>Jam bangun pagi berhasil diatur ke pukul {new_time} WIB.</b>\n"
        f"Setiap jam {new_time} pagi, bot akan membunyikan alarm bangun dan doa menyambut hari baru.",
        parse_mode=ParseMode.HTML
    )
