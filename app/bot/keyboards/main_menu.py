from telegram import ReplyKeyboardMarkup, KeyboardButton


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Menu tombol persisten di bawah chat."""
    keyboard = [
        [
            KeyboardButton("🕌 Jadwal Sholat"),
            KeyboardButton("💧 Catat Minum Air")
        ],
        [
            KeyboardButton("🌱 Pola Hidup Sehat"),
            KeyboardButton("⏰ Set Jam Tidur/Alarm")
        ],
        [
            KeyboardButton("📍 Ganti Kota"),
            KeyboardButton("🔔 Panduan Alarm HP")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
