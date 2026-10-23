import asyncio
import logging
from datetime import datetime
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.services.prayer_service import PrayerService
from app.services.health_service import DOA_TIDUR, DOA_BANGUN_TIDUR
from app.services.audio_service import AudioService
from app.core.timezone import now_local

logger = logging.getLogger(__name__)


def get_prayer_alert_keyboard() -> InlineKeyboardMarkup:
    """Tombol interaktif saat waktu sholat tiba."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Sudah Sholat", callback_data="prayer_done"),
            InlineKeyboardButton("🤲 Doa Setelah Adzan", callback_data="prayer_doa")
        ],
        [
            InlineKeyboardButton("📍 Cek Jadwal Lengkap", callback_data="prayer_schedule_view")
        ]
    ])


def get_water_alert_keyboard() -> InlineKeyboardMarkup:
    """Tombol interaktif saat pengingat minum air."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💧 Catat Minum (+1 Gelas)", callback_data="water_add_one")
        ]
    ])


class SchedulerService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.is_running = False

    async def start(self):
        """Memulai background scheduler async loop."""
        self.is_running = True
        logger.info("Scheduler pengingat sholat, tidur sehat & air minum telah aktif.")
        asyncio.create_task(self._main_routine_loop())

    async def stop(self):
        """Menghentikan scheduler."""
        self.is_running = False
        logger.info("Scheduler dihentikan.")

    async def _main_routine_loop(self):
        """Loop terpusat yang berjalan setiap 60 detik."""
        while self.is_running:
            try:
                await self._check_all_routines()
            except Exception as e:
                logger.error(f"Error pada loop rutinitas: {e}", exc_info=True)

            # Tunggu 60 detik sebelum pengecekan berikutnya
            await asyncio.sleep(60)

    async def _check_all_routines(self):
        """Memeriksa sholat 5 waktu, jam tidur, jam bangun, dan air minum."""
        now_loc = now_local()
        current_time_str = now_loc.strftime("%H:%M")
        current_date_str = now_loc.strftime("%Y-%m-%d")
        current_hour = now_loc.hour
        current_minute = now_loc.minute

        async with AsyncSessionLocal() as session:
            users = (await session.execute(select(User))).scalars().all()

            for user in users:
                if not user.telegram_id:
                    continue

                # -------------------------------------------------------------
                # 1. PENGINGAT SHOLAT 5 WAKTU (AUDIO ADZAN MERDU)
                # -------------------------------------------------------------
                if user.prayer_alert_enabled:
                    city = user.city or "Surabaya"
                    timings = await PrayerService.get_prayer_times(city)

                    for prayer_key in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]:
                        ptime_str = timings.get(prayer_key)
                        if not ptime_str:
                            continue

                        prayer_name = PrayerService.get_indonesian_name(prayer_key)
                        tag_exact = f"{current_date_str}_{prayer_key}_exact"
                        tag_pre = f"{current_date_str}_{prayer_key}_pre"

                        # A. Notifikasi Tepat Saat Adzan (Kirim Audio Adzan)
                        if current_time_str == ptime_str and user.last_reminded_prayer != tag_exact:
                            user.last_reminded_prayer = tag_exact
                            await session.commit()

                            pesan_adzan = (
                                f"📢 <b>WAKTU SHOLAT {prayer_name.upper()} TELAH TIBA!</b>\n"
                                f"📍 Wilayah: <b>{city} & sekitarnya</b> ({ptime_str} WIB)\n\n"
                                f"<i>'Hayya 'alash-shalaah... Hayya 'alal-falaah...'</i>\n"
                                f"Mari hentikan aktivitas sejenak, ambil wudhu, dan tunaikan sholat tepat waktu.\n\n"
                                f"<code>#ALARM_SHOLAT_{prayer_name.upper()}</code>"
                            )
                            await AudioService.send_alert_with_audio(
                                bot=self.bot,
                                chat_id=user.telegram_id,
                                alert_type="adzan",
                                text=pesan_adzan,
                                title=f"Adzan Sholat {prayer_name}",
                                performer=f"Wilayah {city}",
                                reply_markup=get_prayer_alert_keyboard()
                            )

                        # B. Peringatan Persiapan (10 Menit Sebelum Adzan)
                        elif user.prayer_pre_alert_enabled:
                            try:
                                pHour, pMin = map(int, ptime_str.split(":"))
                                p_dt = now_loc.replace(hour=pHour, minute=pMin, second=0, microsecond=0)
                                diff_min = int((p_dt - now_loc).total_seconds() / 60)

                                if 8 <= diff_min <= 10 and user.last_reminded_prayer != tag_pre:
                                    user.last_reminded_prayer = tag_pre
                                    await session.commit()

                                    pesan_pre = (
                                        f"🕌 <b>10 MENIT MENJELANG SHOLAT {prayer_name.upper()}</b>\n"
                                        f"Pukul {ptime_str} WIB ({city})\n\n"
                                        f"Waktunya bersiap-siap, menyelesaikan urusan, dan mengambil air wudhu."
                                    )
                                    await self.bot.send_message(
                                        chat_id=user.telegram_id,
                                        text=pesan_pre,
                                        parse_mode=ParseMode.HTML
                                    )
                            except Exception:
                                pass

                # -------------------------------------------------------------
                # 2. PENGINGAT JAM TIDUR SEHAT (AUDIO RELAKSASI TIDUR)
                # -------------------------------------------------------------
                sleep_target = user.sleep_time or "23:00"
                if user.sleep_reminder_enabled:
                    if current_time_str == sleep_target and user.last_reminded_sleep_date != current_date_str:
                        user.last_reminded_sleep_date = current_date_str
                        await session.commit()

                        pesan_tidur = (
                            f"🌙 <b>WAKTUNYA ISTIRAHAT & TIDUR SEHAT!</b>\n"
                            f"Jam saat ini: <b>{current_time_str} WIB</b>\n\n"
                            f"{DOA_TIDUR}\n\n"
                            f"Selamat beristirahat agar tubuh bugar esok hari! 😴\n\n"
                            f"<code>#ALARM_TIDUR</code>"
                        )
                        await AudioService.send_alert_with_audio(
                            bot=self.bot,
                            chat_id=user.telegram_id,
                            alert_type="sleep",
                            text=pesan_tidur,
                            title="Nada Relaksasi Tidur",
                            performer="Asisten Pola Hidup Sehat"
                        )

                # -------------------------------------------------------------
                # 3. PENGINGAT BANGUN PAGI (AUDIO ALARM JAM WEKER)
                # -------------------------------------------------------------
                wake_target = user.wake_time or "04:30"
                if current_time_str == wake_target and user.last_reminded_wake_date != current_date_str:
                    user.last_reminded_wake_date = current_date_str
                    await session.commit()

                    pesan_bangun = (
                        f"☀️ <b>ALARM BANGUN PAGI!</b>\n"
                        f"Jam saat ini: <b>{current_time_str} WIB</b>\n\n"
                        f"{DOA_BANGUN_TIDUR}\n\n"
                        f"Yuk mulai hari dengan penuh semangat dan energi positif! 💪\n\n"
                        f"<code>#ALARM_BANGUN</code>"
                    )
                    await AudioService.send_alert_with_audio(
                        bot=self.bot,
                        chat_id=user.telegram_id,
                        alert_type="wake",
                        text=pesan_bangun,
                        title="Alarm Bangun Pagi",
                        performer="Asisten Pola Hidup Sehat",
                        reply_markup=get_water_alert_keyboard()
                    )

                # -------------------------------------------------------------
                # 4. PENGINGAT MINUM AIR PUTIH (AUDIO EFEK AIR)
                # -------------------------------------------------------------
                if user.water_reminder_enabled and current_minute == 0:
                    if current_hour in [9, 11, 14, 16, 19] and user.last_reminded_water_hour != current_hour:
                        user.last_reminded_water_hour = current_hour
                        await session.commit()

                        today_glasses = user.water_intake_glasses if user.last_water_date == current_date_str else 0
                        pesan_air = (
                            f"💧 <b>WAKTUNYA MINUM AIR PUTIH!</b>\n\n"
                            f"Tetap terhidrasi agar tubuh tidak mudah lelah dan konsentrasi tetap tajam.\n"
                            f"📊 <i>Progres Hari Ini: {today_glasses} dari {user.water_target_glasses or 8} gelas</i>\n\n"
                            f"<code>#ALARM_MINUM</code>"
                        )
                        await AudioService.send_alert_with_audio(
                            bot=self.bot,
                            chat_id=user.telegram_id,
                            alert_type="water",
                            text=pesan_air,
                            title="Pengingat Minum Air",
                            performer="Hidrasi Sehat",
                            reply_markup=get_water_alert_keyboard()
                        )
