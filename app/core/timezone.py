from datetime import datetime, timezone
import zoneinfo
from app.core.config import settings


def get_user_tz(tz_str: str = None) -> zoneinfo.ZoneInfo:
    """Mengembalikan objek ZoneInfo, default Asia/Jakarta (WIB)."""
    tz_name = tz_str or settings.TIMEZONE or "Asia/Jakarta"
    try:
        return zoneinfo.ZoneInfo(tz_name)
    except Exception:
        return zoneinfo.ZoneInfo("Asia/Jakarta")


def now_local(tz_str: str = None) -> datetime:
    """Mengembalikan waktu saat ini dalam zona waktu lokal pengguna."""
    return datetime.now(get_user_tz(tz_str))


def to_utc(dt: datetime, tz_str: str = None) -> datetime:
    """Mengonversi datetime lokal ke datetime UTC (naive atau aware)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Jika naive, asumsikan zona waktu lokal
        dt = dt.replace(tzinfo=get_user_tz(tz_str))
    return dt.astimezone(timezone.utc)


def to_local(dt: datetime, tz_str: str = None) -> datetime:
    """Mengonversi datetime UTC ke datetime lokal pengguna."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(get_user_tz(tz_str))


def format_dt(dt: datetime, tz_str: str = None, include_time: bool = True) -> str:
    """Format datetime ke teks ramah bahasa Indonesia."""
    if dt is None:
        return "-"
    local_dt = to_local(dt, tz_str)

    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    months = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]

    day_name = days[local_dt.weekday()]
    month_name = months[local_dt.month]

    if include_time:
        return f"{day_name}, {local_dt.day} {month_name} {local_dt.year} pukul {local_dt.strftime('%H:%M')} WIB"
    return f"{day_name}, {local_dt.day} {month_name} {local_dt.year}"
