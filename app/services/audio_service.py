import os
import logging
from typing import Optional
from telegram import Bot, InlineKeyboardMarkup
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

# Direktori aset audio
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIO_DIR = os.path.join(BASE_DIR, "assets", "audio")


class AudioService:
    @staticmethod
    async def send_alert_with_audio(
        bot: Bot,
        chat_id: int,
        alert_type: str,
        text: str,
        title: str = "Pengingat",
        performer: str = "Asisten Bot",
        reply_markup: Optional[InlineKeyboardMarkup] = None
    ):
        """
        Mengirim notifikasi yang disertai file audio berbeda sesuai jenis alert:
        - 'adzan': Audio Adzan Merdu (adzan.mp3)
        - 'wake': Suara Alarm Jam Weker (wake.mp3)
        - 'sleep': Suara Melodi Tidur Rileks (sleep.wav)
        - 'water': Suara Efek Tetesan Air Segar (water.wav)
        """
        file_map = {
            "adzan": ("adzan.mp3", "Adzan Merdu", "Ibadah Sholat 5 Waktu"),
            "wake": ("wake.mp3", "Alarm Bangun Pagi", "Rutinitas Sehat"),
            "sleep": ("sleep.wav", "Nada Relaksasi Tidur", "Pola Tidur Sehat"),
            "water": ("water.wav", "Efek Tetesan Air", "Hidrasi Sehat")
        }

        audio_info = file_map.get(alert_type)
        if not audio_info:
            # Fallback jika jenis audio tidak dikenali
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            return

        filename, default_title, default_performer = audio_info
        file_path = os.path.join(AUDIO_DIR, filename)

        if not os.path.exists(file_path):
            logger.warning(f"File audio tidak ditemukan: {file_path}, mengirim teks biasa.")
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            return

        try:
            with open(file_path, "rb") as audio_file:
                await bot.send_audio(
                    chat_id=chat_id,
                    audio=audio_file,
                    caption=text,
                    title=title or default_title,
                    performer=performer or default_performer,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.error(f"Gagal mengirim audio ({alert_type}) ke {chat_id}: {e}. Mencoba fallback teks...")
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            except Exception as e2:
                logger.error(f"Gagal mengirim pesan fallback: {e2}")
