from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from app.core.database import AsyncSessionLocal
from app.services.task_service import TaskService
from app.services.health_service import DOA_SETELAH_ADZAN, TIPS_HIDUP_SEHAT
from app.bot.handlers.prayer_handler import show_prayer_schedule, alarm_guide_handler
from app.bot.handlers.health_handler import (
    show_health_dashboard,
    add_water_handler,
    sleep_settings_handler
)


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Router terpusat untuk semua aksi tombol inline keyboard."""
    query = update.callback_query
    if not query:
        return

    data = query.data
    user = update.effective_user

    async with AsyncSessionLocal() as session:
        db_user = await TaskService.get_or_create_user(session, user.id, user.username, user.full_name)

    # 1. Sholat & Doa
    if data == "prayer_done":
        await query.answer("Alhamdulillah! Semoga amal ibadah sholat Anda diterima Allah SWT. 🤲", show_alert=True)
        return

    elif data == "prayer_doa":
        await query.answer()
        await query.message.reply_text(DOA_SETELAH_ADZAN, parse_mode=ParseMode.HTML)
        return

    elif data == "prayer_schedule_view":
        await query.answer()
        await show_prayer_schedule(update, context)
        return

    elif data == "change_city_prompt":
        await query.answer()
        teks = (
            "📍 <b>GANTI KOTA JADWAL SHOLAT</b>\n\n"
            "Ketik perintah:\n"
            "<code>/kota &lt;Nama Kota&gt;</code>\n\n"
            "Contoh: <code>/kota Surabaya</code> atau <code>/kota Jakarta</code>"
        )
        await query.message.reply_text(teks, parse_mode=ParseMode.HTML)
        return

    elif data == "show_alarm_guide":
        await alarm_guide_handler(update, context)
        return

    # 2. Pola Hidup Sehat & Air Minum
    elif data == "water_add_one":
        await add_water_handler(update, context)
        return

    elif data == "open_health_dash":
        await query.answer()
        await show_health_dashboard(update, context)
        return

    elif data == "show_sleep_settings":
        await query.answer()
        await sleep_settings_handler(update, context)
        return

    # 3. Ubah Jam Tidur Instan dari Tombol Preset
    elif data.startswith("setsleep_"):
        new_sleep = data.replace("setsleep_", "")
        async with AsyncSessionLocal() as session:
            user_obj = await TaskService.get_or_create_user(session, user.id)
            user_obj.sleep_time = new_sleep
            await session.commit()

        await query.answer(f"✅ Jam tidur diatur ke pukul {new_sleep} WIB!", show_alert=True)
        await sleep_settings_handler(update, context)
        return

    # 4. Ubah Jam Bangun Instan dari Tombol Preset
    elif data.startswith("setwake_"):
        new_wake = data.replace("setwake_", "")
        async with AsyncSessionLocal() as session:
            user_obj = await TaskService.get_or_create_user(session, user.id)
            user_obj.wake_time = new_wake
            await session.commit()

        await query.answer(f"✅ Jam bangun diatur ke pukul {new_wake} WIB!", show_alert=True)
        await sleep_settings_handler(update, context)
        return

    elif data == "tip_screen":
        await query.answer()
        await query.message.reply_text(
            f"👀 <b>Tips Kesehatan Mata:</b>\n\n{TIPS_HIDUP_SEHAT[1]}\n\n"
            f"Istirahatkan mata sejenak agar tidak lelah dan tegang!",
            parse_mode=ParseMode.HTML
        )
        return

    elif data == "tip_nutrition":
        await query.answer()
        await query.message.reply_text(
            f"🥗 <b>Tips Nutrisi Seimbang:</b>\n\n{TIPS_HIDUP_SEHAT[3]}\n\n"
            f"Awali hari dengan sarapan bergizi untuk menjaga energi Anda seharian!",
            parse_mode=ParseMode.HTML
        )
        return

    await query.answer()
