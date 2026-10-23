import asyncio
from datetime import datetime, timedelta, timezone

try:
    import pytest
except ImportError:
    pytest = None

from app.core.database import init_db, AsyncSessionLocal
from app.services.task_service import TaskService
from app.services.lms_service import clean_html, parse_course_and_title
from app.schemas.task import TaskCreate


async def test_database_and_task_crud():
    # 1. Inisialisasi DB
    await init_db()

    async with AsyncSessionLocal() as session:
        # 2. Buat User
        user = await TaskService.get_or_create_user(
            session=session,
            telegram_id=999888777,
            username="test_student",
            full_name="Mahasiswa Test"
        )
        assert user.id is not None
        assert user.telegram_id == 999888777

        # 3. Buat Tugas
        due_time = datetime.now(timezone.utc) + timedelta(days=1)
        task_in = TaskCreate(
            title="Tugas Pemrograman Python",
            description="Membuat bot asisten manajemen tugas",
            course_name="Algoritma & Pemrograman",
            due_datetime=due_time,
            priority="HIGH",
            source="MANUAL"
        )

        task = await TaskService.create_task(session, user.id, task_in)
        assert task.id is not None
        assert task.title == "Tugas Pemrograman Python"
        assert task.is_completed is False

        # 4. List Tugas
        tasks = await TaskService.list_tasks(session, user.id, "active")
        assert len(tasks) >= 1

        # 5. Toggle Complete
        updated_task = await TaskService.toggle_complete(session, task.id, user.id)
        assert updated_task.is_completed is True

        # 6. Delete Task
        deleted = await TaskService.delete_task(session, task.id, user.id)
        assert deleted is True


def test_lms_html_cleaner():
    html_text = "<p>Silakan upload file laporan <b>PDF</b> di sini.<br>Deadline tidak ada toleransi.</p>"
    cleaned = clean_html(html_text)
    assert "<p>" not in cleaned
    assert "<b>" not in cleaned
    assert "Silakan upload file laporan" in cleaned


def test_lms_summary_parser():
    # Format [Mata Kuliah] Nama Tugas
    raw = "[Kecerdasan Buatan] Tugas 2 - Neural Network is due"
    course, title = parse_course_and_title(raw)
    assert course == "Kecerdasan Buatan"
    assert title == "Tugas 2 - Neural Network"

    # Format 'Mata Kuliah - Nama Tugas'
    raw2 = "Metodologi Penelitian - Proposal Skripsi"
    course2, title2 = parse_course_and_title(raw2)
    assert course2 == "Metodologi Penelitian"
    assert title2 == "Proposal Skripsi"


if __name__ == "__main__":
    asyncio.run(test_database_and_task_crud())
    test_lms_html_cleaner()
    test_lms_summary_parser()
    print("Semua tes unit dan integrasi berhasil!")
