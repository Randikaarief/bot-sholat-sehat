from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from app.models.task import Task


def get_task_filter_keyboard(current_filter: str = "active") -> InlineKeyboardMarkup:
    """Keyboard navigasi filter tugas."""
    def mark(filter_name: str, label: str) -> str:
        return f"👉 {label}" if current_filter == filter_name else label

    buttons = [
        [
            InlineKeyboardButton(mark("today", "📅 Hari Ini"), callback_data="filter_today"),
            InlineKeyboardButton(mark("upcoming", "⏳ Mendatang"), callback_data="filter_upcoming"),
        ],
        [
            InlineKeyboardButton(mark("overdue", "⚠️ Terlewat"), callback_data="filter_overdue"),
            InlineKeyboardButton(mark("completed", "✅ Selesai"), callback_data="filter_completed"),
        ],
        [
            InlineKeyboardButton(mark("active", "📋 Semua Aktif"), callback_data="filter_active"),
            InlineKeyboardButton("➕ Tambah Manual", callback_data="task_new_manual"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def get_task_actions_keyboard(task: Task) -> InlineKeyboardMarkup:
    """Keyboard aksi interaktif untuk satu tugas spesifik."""
    buttons = []

    # Baris 1: Selesai / Belum Selesai
    if task.is_completed:
        buttons.append([
            InlineKeyboardButton("↩️ Buka Kembali", callback_data=f"toggle_{task.id}"),
            InlineKeyboardButton("🗑️ Hapus Tugas", callback_data=f"del_confirm_{task.id}")
        ])
    else:
        buttons.append([
            InlineKeyboardButton("✅ Tandai Selesai", callback_data=f"toggle_{task.id}"),
            InlineKeyboardButton("🗑️ Hapus Tugas", callback_data=f"del_confirm_{task.id}")
        ])
        # Baris 2: Tombol Cepat Snooze
        buttons.append([
            InlineKeyboardButton("💤 +10m", callback_data=f"snooze_{task.id}_10"),
            InlineKeyboardButton("💤 +1 Jam", callback_data=f"snooze_{task.id}_60"),
            InlineKeyboardButton("💤 Besok", callback_data=f"snooze_{task.id}_1440"),
        ])

    buttons.append([
        InlineKeyboardButton("🔙 Kembali ke Daftar", callback_data="filter_active")
    ])

    return InlineKeyboardMarkup(buttons)


def get_reminder_alert_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Keyboard yang dikirimkan bersama notifikasi pengingat tepat waktu."""
    buttons = [
        [
            InlineKeyboardButton("✅ Selesai", callback_data=f"toggle_{task_id}"),
            InlineKeyboardButton("💤 Tunda 10 Menit", callback_data=f"snooze_{task_id}_10"),
        ],
        [
            InlineKeyboardButton("💤 Tunda 1 Jam", callback_data=f"snooze_{task_id}_60"),
            InlineKeyboardButton("💤 Tunda Besok", callback_data=f"snooze_{task_id}_1440"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def get_delete_confirm_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Dialog konfirmasi penghapusan tugas."""
    buttons = [
        [
            InlineKeyboardButton("⚠️ Ya, Hapus!", callback_data=f"del_yes_{task_id}"),
            InlineKeyboardButton("❌ Batal", callback_data=f"view_{task_id}")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def get_lms_menu_keyboard(has_url: bool = False) -> InlineKeyboardMarkup:
    """Menu tombol interaktif untuk fitur LMS Vinesa UNESA."""
    buttons = []
    if has_url:
        buttons.append([
            InlineKeyboardButton("🔄 Sinkronkan Sekarang", callback_data="lms_sync_now")
        ])
        buttons.append([
            InlineKeyboardButton("✏️ Ubah Link iCal", callback_data="lms_change_url"),
            InlineKeyboardButton("❌ Putuskan LMS", callback_data="lms_disconnect")
        ])
    else:
        buttons.append([
            InlineKeyboardButton("🔗 Hubungkan Link iCal Vinesa", callback_data="lms_connect_info")
        ])
    buttons.append([
        InlineKeyboardButton("📖 Panduan Ambil Link Vinesa", callback_data="lms_guide")
    ])
    return InlineKeyboardMarkup(buttons)
