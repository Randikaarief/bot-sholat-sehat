from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from app.core.database import AsyncSessionLocal
from app.services.task_service import TaskService
from app.core.timezone import format_dt, now_local, to_local
from app.bot.keyboards.task_keyboards import (
    get_task_filter_keyboard,
    get_task_actions_keyboard
)


def format_task_preview(task, tz_str: str = "Asia/Jakarta") -> str:
    """Format satu baris ringkas untuk daftar tugas."""
    icon_prio = "🔴" if task.priority == "HIGH" else ("🟡" if task.priority == "MEDIUM" else "🟢")

    is_overdue = False
    if task.due_datetime and not task.is_completed:
        due_aware = task.due_datetime.replace(tzinfo=timezone.utc) if task.due_datetime.tzinfo is None else task.due_datetime
        if due_aware < datetime.now(timezone.utc):
            is_overdue = True

    icon_status = "✅" if task.is_completed else ("⚠️" if is_overdue else "⏳")

    source_badge = ""
    if task.source == "LMS_VINESA":
        source_badge = " [🎓 Vinesa]"
    elif task.source == "VISION":
        source_badge = " [📷 Foto]"

    due_str = f" • ⏰ {format_dt(task.due_datetime, tz_str)}" if task.due_datetime else " • ⏰ Tanpa deadline"
    return f"{icon_status} {icon_prio} <b>{task.title}</b>{source_badge}{due_str}"


async def render_task_list(user_id: int, filter_type: str = "active") -> tuple[str, InlineKeyboardMarkup]:
    """Helper untuk merender teks dan keyboard daftar tugas."""
    filter_labels = {
        "today": "📅 Tugas Hari Ini",
        "upcoming": "⏳ Tugas Mendatang",
        "overdue": "⚠️ Tugas Terlewat (Overdue)",
        "completed": "✅ Tugas Selesai",
        "active": "📋 Semua Tugas Aktif"
    }

    async with AsyncSessionLocal() as session:
        tasks = await TaskService.list_tasks(session, user_id, filter_type=filter_type)

    header = f"<b>{filter_labels.get(filter_type, '📋 Daftar Tugas')}</b>\n"
    header += f"<i>Total: {len(tasks)} tugas</i>\n\n"

    if not tasks:
        body = "<i>Tidak ada tugas pada kategori ini.</i>\n\n"
        keyboard = get_task_filter_keyboard(filter_type)
        return header + body, keyboard

    body_lines = []
    item_buttons = []

    for idx, t in enumerate(tasks[:15], 1):
        line = f"<b>{idx}.</b> {format_task_preview(t)}"
        body_lines.append(line)
        # Tombol aksi cepat untuk tiap tugas (maksimal 15 agar tidak overload)
        btn_label = f"#{idx} {t.title[:20]}"
        item_buttons.append(InlineKeyboardButton(btn_label, callback_data=f"view_{t.id}"))

    # Susun tombol tugas dalam 2 kolom
    button_rows = [item_buttons[i:i + 2] for i in range(0, len(item_buttons), 2)]

    # Tambahkan filter navigasi di bagian bawah
    filter_kb = get_task_filter_keyboard(filter_type)
    all_rows = button_rows + filter_kb.inline_keyboard

    full_text = header + "\n".join(body_lines) + "\n\n💡 <i>Klik tombol nomor tugas di bawah untuk melihat detail, snooze, atau menyelesaikan.</i>"
    return full_text, InlineKeyboardMarkup(all_rows)


async def tasks_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani perintah /tugas atau menu '📋 Daftar Tugas'."""
    user = update.effective_user
    if not user:
        return

    async with AsyncSessionLocal() as session:
        db_user = await TaskService.get_or_create_user(session, user.id, user.username, user.full_name)

    text, keyboard = await render_task_list(db_user.id, "active")
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )


async def summary_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani rekap harian (/rekap atau menu '📊 Rekap Hari Ini')."""
    user = update.effective_user
    if not user:
        return

    async with AsyncSessionLocal() as session:
        db_user = await TaskService.get_or_create_user(session, user.id, user.username, user.full_name)
        data = await TaskService.get_summary_data(session, db_user.id)

    now_loc = now_local()
    teks = (
        f"📊 <b>RINGKASAN AGENDA & TUGAS</b>\n"
        f"📅 <i>{format_dt(now_loc, include_time=False)}</i>\n\n"
    )

    if data["total_active"] == 0:
        teks += "🎉 <b>Semua tugas tuntas!</b> Tidak ada tugas aktif yang tertunda saat ini.\n"
    else:
        # 1. Overdue
        if data["overdue"]:
            teks += f"⚠️ <b>PERLU PERHATIAN (Terlewat - {len(data['overdue'])}):</b>\n"
            for t in data["overdue"]:
                teks += f"• 🔴 <b>{t.title}</b> (Deadline: {format_dt(t.due_datetime)})\n"
            teks += "\n"

        # 2. Hari ini
        teks += f"📌 <b>JATUH TEMPO HARI INI ({len(data['today'])}):</b>\n"
        if data["today"]:
            for t in data["today"]:
                prio = "🔴" if t.priority == "HIGH" else "🟡"
                teks += f"• {prio} <b>{t.title}</b> ({format_dt(t.due_datetime)})\n"
        else:
            teks += "<i>Tidak ada tugas yang jatuh tempo hari ini.</i>\n"
        teks += "\n"

        # 3. Mendatang
        if data["upcoming"]:
            teks += f"⏳ <b>MENDATANG ({len(data['upcoming'])}):</b>\n"
            for t in data["upcoming"]:
                teks += f"• 🟢 <b>{t.title}</b> ({format_dt(t.due_datetime)})\n"
            teks += "\n"

    teks += "Tetap semangat dan selesaikan tugasmu tepat waktu! 💪"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Buka Daftar Tugas", callback_data="filter_active")]
    ])

    await update.message.reply_text(
        text=teks,
        parse_mode=ParseMode.HTML,
        reply_markup=kb
    )
