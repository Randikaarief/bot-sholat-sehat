import re
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
import httpx
import icalendar
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.user import User
from app.core.timezone import to_utc

logger = logging.getLogger(__name__)


def clean_html(raw_html: str) -> str:
    """Membersihkan tag HTML yang sering disertakan oleh Moodle/Vinesa."""
    if not raw_html:
        return ""
    # Ganti <br> atau <p> dengan newline
    text = re.sub(r'<\s*br\s*/?>', '\n', raw_html, flags=re.IGNORECASE)
    text = re.sub(r'<\s*/p\s*>', '\n', text, flags=re.IGNORECASE)
    # Hapus semua tag html lainnya
    clean = re.sub(r'<.*?>', '', text)
    # Bersihkan whitespace berlebih
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    return "\n".join(lines)


def parse_course_and_title(raw_summary: str) -> Tuple[Optional[str], str]:
    """
    Moodle sering menyusun summary seperti:
    '[Nama MK] Judul Tugas is due' atau 'Tugas 1 - Pemrograman Web'
    """
    summary = raw_summary.strip()
    # Bersihkan suffix 'is due' atau 'jatuh tempo'
    summary = re.sub(r'\s+is due$', '', summary, flags=re.IGNORECASE)
    summary = re.sub(r'\s+jatuh tempo$', '', summary, flags=re.IGNORECASE)

    # Deteksi format [Mata Kuliah] Nama Tugas
    match_bracket = re.match(r'^\[(.*?)\]\s*(.*)$', summary)
    if match_bracket:
        return match_bracket.group(1).strip(), match_bracket.group(2).strip()

    # Deteksi pemisah strip 'Nama MK - Judul Tugas' atau sebaliknya
    if " - " in summary:
        parts = summary.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()

    return None, summary


class LMSService:
    @staticmethod
    async def fetch_ical_content(url: str) -> Optional[str]:
        """Mengunduh konten kalender .ics dari link Vinesa Moodle secara aman."""
        # Ganti webcal:// menjadi https:// jika user copy format webcal
        if url.startswith("webcal://"):
            url = "https://" + url[9:]

        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            try:
                response = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) VinesaBot/1.0"})
                if response.status_code == 200:
                    return response.text
                logger.error(f"Gagal mengunduh iCal: Status HTTP {response.status_code}")
                return None
            except Exception as e:
                logger.error(f"Error saat mengunduh iCal dari {url}: {e}")
                return None

    @staticmethod
    async def sync_user_lms(session: AsyncSession, user: User) -> Tuple[int, str]:
        """
        Menyinkronkan tugas dari link iCal Vinesa UNESA milik user.
        Mengembalikan (jumlah_tugas_baru, pesan_status).
        """
        if not user.lms_ical_url:
            return 0, "Anda belum menautkan link iCal Vinesa. Gunakan perintah /link_lms."

        content = await LMSService.fetch_ical_content(user.lms_ical_url)
        if not content:
            return 0, "Gagal mengambil data dari server LMS Vinesa. Pastikan URL iCal masih valid."

        try:
            cal = icalendar.Calendar.from_ical(content)
        except Exception as e:
            logger.error(f"Gagal membaca format iCal: {e}")
            return 0, f"Format kalender tidak dikenali: {e}"

        now_utc = datetime.now(timezone.utc)
        new_tasks_count = 0

        for component in cal.walk():
            if component.name == "VEVENT":
                uid = str(component.get("uid", "")).strip()
                summary_raw = str(component.get("summary", "")).strip()
                description_raw = str(component.get("description", "")).strip()

                # Tanggal tenggat waktu (DTEND atau DTSTART)
                dtend = component.get("dtend") or component.get("dtstart")
                due_dt = None
                if dtend:
                    dt_val = dtend.dt
                    if isinstance(dt_val, datetime):
                        due_dt = to_utc(dt_val)
                    else:
                        # Jika tanggal saja (date), jadikan jam 23:59:59 lokal
                        due_dt = to_utc(datetime.combine(dt_val, datetime.max.time().replace(microsecond=0)))

                # Abaikan tugas yang sudah lewat lebih dari 7 hari lalu
                if due_dt and (now_utc - due_dt).days > 7:
                    continue

                # Cek apakah tugas dengan external_uid ini sudah ada di database untuk user ini
                stmt = select(Task).where(
                    and_(
                        Task.user_id == user.id,
                        Task.external_uid == uid
                    )
                )
                existing = (await session.execute(stmt)).scalar_one_or_none()

                if not existing and uid:
                    course_name, task_title = parse_course_and_title(summary_raw)
                    cleaned_desc = clean_html(description_raw)

                    new_task = Task(
                        user_id=user.id,
                        title=task_title or summary_raw,
                        description=cleaned_desc if cleaned_desc else None,
                        course_name=course_name,
                        source="LMS_VINESA",
                        external_uid=uid,
                        due_datetime=due_dt,
                        priority="HIGH" if "kuis" in (task_title or "").lower() or "exam" in (task_title or "").lower() else "MEDIUM",
                        is_completed=False
                    )
                    session.add(new_task)
                    new_tasks_count += 1

        user.last_lms_sync = now_utc
        await session.commit()
        return new_tasks_count, f"Berhasil sinkronisasi. {new_tasks_count} tugas baru ditemukan."
