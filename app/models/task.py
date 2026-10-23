from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    course_name = Column(String(150), nullable=True)  # Mata kuliah (jika dari LMS/kuliah)
    source = Column(String(50), default="MANUAL")     # MANUAL, NLP, VISION, LMS_VINESA

    # ID unik event iCal dari Moodle Vinesa untuk mencegah entri ganda
    external_uid = Column(String(255), nullable=True, index=True)

    due_datetime = Column(DateTime(timezone=True), nullable=True, index=True)
    priority = Column(String(20), default="MEDIUM")   # LOW, MEDIUM, HIGH

    is_completed = Column(Boolean, default=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Status pelacakan pengingat (notifikasi berjenjang)
    reminded_h1 = Column(Boolean, default=False)      # H-1 hari (24 jam)
    reminded_1h = Column(Boolean, default=False)      # H-1 jam (60 menit)
    reminded_15m = Column(Boolean, default=False)     # H-15 menit
    reminded_due = Column(Boolean, default=False)     # Saat deadline tiba
    snoozed_until = Column(DateTime(timezone=True), nullable=True)  # Waktu pengingat tunda

    user = relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"<Task id={self.id} title='{self.title}' due={self.due_datetime} completed={self.is_completed}>"
