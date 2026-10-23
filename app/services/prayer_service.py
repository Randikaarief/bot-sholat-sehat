import logging
from datetime import datetime, date
from typing import Dict, Optional
import httpx
from app.core.timezone import now_local

logger = logging.getLogger(__name__)

# Cache harian: { "Surabaya_2026-10-23": { ...timings... } }
_PRAYER_CACHE: Dict[str, dict] = {}

# Fallback jadwal standar jika offline (Zona WIB - Estimasi Surabaya)
FALLBACK_TIMINGS = {
    "Fajr": "04:05",
    "Sunrise": "05:20",
    "Dhuhr": "11:32",
    "Asr": "14:48",
    "Maghrib": "17:39",
    "Isha": "18:50"
}

NAMA_SHOLAT_ID = {
    "Fajr": "Subuh",
    "Sunrise": "Terbit (Syuruq)",
    "Dhuhr": "Dzuhur",
    "Asr": "Ashar",
    "Maghrib": "Maghrib",
    "Isha": "Isya"
}


class PrayerService:
    @staticmethod
    async def get_prayer_times(city: str = "Surabaya") -> Dict[str, str]:
        """
        Mengambil jadwal sholat hari ini untuk kota tertentu dari API Aladhan (Metode Kemenag/Indonesia).
        """
        today_str = now_local().strftime("%Y-%m-%d")
        cache_key = f"{city.lower()}_{today_str}"

        if cache_key in _PRAYER_CACHE:
            return _PRAYER_CACHE[cache_key]

        url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=Indonesia&method=11"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    timings = data.get("data", {}).get("timings", {})
                    if timings:
                        # Bersihkan format waktu (ambil HH:MM saja)
                        clean_timings = {
                            "Fajr": timings.get("Fajr", "04:05")[:5],
                            "Sunrise": timings.get("Sunrise", "05:20")[:5],
                            "Dhuhr": timings.get("Dhuhr", "11:32")[:5],
                            "Asr": timings.get("Asr", "14:48")[:5],
                            "Maghrib": timings.get("Maghrib", "17:39")[:5],
                            "Isha": timings.get("Isha", "18:50")[:5]
                        }
                        _PRAYER_CACHE[cache_key] = clean_timings
                        logger.info(f"Berhasil memuat jadwal sholat untuk kota {city}: {clean_timings}")
                        return clean_timings
        except Exception as e:
            logger.error(f"Gagal mengambil jadwal sholat dari API untuk kota {city}: {e}")

        # Gunakan fallback jika gagal koneksi
        return FALLBACK_TIMINGS

    @staticmethod
    def get_indonesian_name(prayer_key: str) -> str:
        """Mengonversi nama sholat ke Bahasa Indonesia."""
        return NAMA_SHOLAT_ID.get(prayer_key, prayer_key)
