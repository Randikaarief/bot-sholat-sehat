from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.timezone import now_local


DOA_SETELAH_ADZAN = (
    "🤲 <b>Doa Setelah Mendengar Adzan:</b>\n\n"
    "<i>Allahumma rabba hadzihid da’watit tammah, wash-shalatil qaa-imah, "
    "aati Muhammadanil washilata wal fadhilah, wab’atshu maqaamam mahmuda alladzi wa’adtah.</i>\n\n"
    "<b>Artinya:</b>\n"
    "<i>'Ya Allah, Tuhan pemilik panggilan yang sempurna ini dan sholat yang didirikan, "
    "berilah Nabi Muhammad wasilah dan keutamaan, serta tempatkanlah ia pada kedudukan yang terpuji yang telah Engkau janjikan.'</i> (HR. Bukhari)"
)

DOA_TIDUR = (
    "🌙 <b>Doa Sebelum Tidur:</b>\n\n"
    "<i>Bismika Allahumma ahya wa bismika amuut.</i>\n"
    "<i>'Dengan nama-Mu ya Allah, aku hidup dan aku mati.'</i> (HR. Bukhari & Muslim)\n\n"
    "💡 <b>Tips Pola Tidur Sehat:</b>\n"
    "• Jauhkan layar HP minimal 30 menit sebelum tidur.\n"
    "• Matikan lampu kamar untuk memicu hormon melatonin.\n"
    "• Lakukan relaksasi / wudhu sebelum tidur."
)

DOA_BANGUN_TIDUR = (
    "☀️ <b>Doa Bangun Tidur:</b>\n\n"
    "<i>Alhamdulillahilladzi ahyana ba’da ma amatana wa ilaihin nusyur.</i>\n"
    "<i>'Segala puji bagi Allah yang telah menghidupkan kami setelah mematikan kami, dan kepada-Nya kami kembali.'</i>\n\n"
    "💧 Awali hari dengan minum segelas air putih hangat!"
)

TIPS_HIDUP_SEHAT = [
    "💧 <b>Aturan Minum Air Putih:</b> Targetkan 8 gelas (2 liter) per hari untuk menjaga metabolisme tubuh dan fokus kerja.",
    "👀 <b>Aturan 20-20-20:</b> Setiap 20 menit menatap layar, istirahatkan mata dengan melihat objek berjarak 20 kaki (6 meter) selama 20 detik.",
    "🚶‍♂️ <b>Peregangan Ringan:</b> Bangkit dari kursi setiap 1-2 jam dan regangkan otot punggung serta leher.",
    "🥗 <b>Pola Makan Teratur:</b> Jangan lewatkan sarapan pagi dan perbanyak porsi sayuran hijau serta serat."
]


class HealthService:
    @staticmethod
    async def log_water(session: AsyncSession, user: User) -> tuple[int, int]:
        """Menambah 1 gelas minum air putih untuk hari ini."""
        today_str = now_local().strftime("%Y-%m-%d")

        # Jika hari berganti, reset hitungan
        if user.last_water_date != today_str:
            user.water_intake_glasses = 1
            user.last_water_date = today_str
        else:
            user.water_intake_glasses = (user.water_intake_glasses or 0) + 1

        await session.commit()
        await session.refresh(user)
        return user.water_intake_glasses, user.water_target_glasses or 8

    @staticmethod
    async def get_health_status(session: AsyncSession, user: User) -> dict:
        """Mengambil ringkasan pola hidup sehat hari ini."""
        today_str = now_local().strftime("%Y-%m-%d")
        glasses = user.water_intake_glasses if user.last_water_date == today_str else 0
        target = user.water_target_glasses or 8

        return {
            "water_glasses": glasses,
            "water_target": target,
            "water_percent": min(100, int((glasses / target) * 100)),
            "sleep_time": user.sleep_time,
            "wake_time": user.wake_time,
            "city": user.city
        }
