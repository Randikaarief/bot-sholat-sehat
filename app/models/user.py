from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    timezone = Column(String(50), default="Asia/Jakarta")

    # Lokasi untuk Jadwal Sholat
    city = Column(String(100), default="Surabaya")

    # Pengaturan Pengingat Sholat 5 Waktu
    prayer_alert_enabled = Column(Boolean, default=True)
    prayer_pre_alert_enabled = Column(Boolean, default=True)  # 10 menit sebelum adzan
    last_reminded_prayer = Column(String(50), default="")     # misal "2026-10-23_Asr"

    # Pengaturan Jam Tidur Sehat & Bangun
    sleep_reminder_enabled = Column(Boolean, default=True)
    sleep_time = Column(String(10), default="23:00")          # Jam tidur malam (Default 23:00 WIB)
    wake_time = Column(String(10), default="04:30")           # Jam bangun pagi
    last_reminded_sleep_date = Column(String(20), default="")
    last_reminded_wake_date = Column(String(20), default="")

    # Pengaturan Pola Hidup Sehat & Minum Air
    water_reminder_enabled = Column(Boolean, default=True)
    water_intake_glasses = Column(Integer, default=0)
    water_target_glasses = Column(Integer, default=8)
    last_water_date = Column(String(20), default="")
    last_reminded_water_hour = Column(Integer, default=-1)

    # LMS SSO UNESA / Vinesa Moodle (tetap dipertahankan sebagai opsi)
    lms_ical_url = Column(Text, nullable=True)
    last_lms_sync = Column(DateTime(timezone=True), nullable=True)

    # Pengaturan Rekap Pagi
    morning_digest_enabled = Column(Boolean, default=True)
    morning_digest_time = Column(String(10), default="07:00")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User telegram_id={self.telegram_id} username={self.username} city={self.city}>"
