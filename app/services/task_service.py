from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.core.timezone import now_local, to_utc, to_local


class TaskService:
    @staticmethod
    async def get_or_create_user(
        session: AsyncSession,
        telegram_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None
    ) -> User:
        """Mendapatkan atau membuat user baru berdasarkan ID Telegram."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                timezone="Asia/Jakarta",
                morning_digest_enabled=True,
                morning_digest_time="07:00"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            # Perbarui username atau full_name jika berubah
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                updated = True
            if updated:
                await session.commit()
                await session.refresh(user)
        return user

    @staticmethod
    async def create_task(
        session: AsyncSession,
        user_id: int,
        task_in: TaskCreate
    ) -> Task:
        """Membuat tugas baru."""
        # Pastikan due_datetime dikonversi ke UTC untuk konsistensi database
        utc_due = to_utc(task_in.due_datetime) if task_in.due_datetime else None

        task = Task(
            user_id=user_id,
            title=task_in.title,
            description=task_in.description,
            course_name=task_in.course_name,
            source=task_in.source,
            external_uid=task_in.external_uid,
            due_datetime=utc_due,
            priority=task_in.priority,
            is_completed=False
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task

    @staticmethod
    async def get_task(session: AsyncSession, task_id: int, user_id: int) -> Optional[Task]:
        """Mengambil detail satu tugas milik user."""
        stmt = select(Task).where(and_(Task.id == task_id, Task.user_id == user_id))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_tasks(
        session: AsyncSession,
        user_id: int,
        filter_type: str = "active",
        limit: int = 50
    ) -> List[Task]:
        """Mengambil daftar tugas user berdasarkan filter."""
        now_dt = datetime.now(timezone.utc)
        now_loc = now_local()
        start_of_today_loc = now_loc.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_today_loc = start_of_today_loc + timedelta(days=1)
        start_of_today_utc = to_utc(start_of_today_loc)
        end_of_today_utc = to_utc(end_of_today_loc)

        query = select(Task).where(Task.user_id == user_id)

        if filter_type == "today":
            # Tugas aktif yang jatuh tempo hari ini
            query = query.where(
                and_(
                    Task.is_completed == False,
                    Task.due_datetime >= start_of_today_utc,
                    Task.due_datetime < end_of_today_utc
                )
            ).order_by(asc(Task.due_datetime))
        elif filter_type == "upcoming":
            # Tugas aktif yang jatuh tempo setelah hari ini
            query = query.where(
                and_(
                    Task.is_completed == False,
                    Task.due_datetime >= end_of_today_utc
                )
            ).order_by(asc(Task.due_datetime))
        elif filter_type == "overdue":
            # Tugas aktif yang sudah lewat tenggat
            query = query.where(
                and_(
                    Task.is_completed == False,
                    Task.due_datetime < now_dt
                )
            ).order_by(desc(Task.due_datetime))
        elif filter_type == "completed":
            # Tugas yang sudah selesai
            query = query.where(Task.is_completed == True).order_by(desc(Task.completed_at)).limit(limit)
        else:
            # Semua tugas aktif (default)
            query = query.where(Task.is_completed == False).order_by(
                Task.due_datetime.asc().nulls_last()
            ).limit(limit)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def toggle_complete(session: AsyncSession, task_id: int, user_id: int) -> Optional[Task]:
        """Mengubah status tugas menjadi selesai atau belum selesai."""
        task = await TaskService.get_task(session, task_id, user_id)
        if not task:
            return None

        task.is_completed = not task.is_completed
        if task.is_completed:
            task.completed_at = datetime.now(timezone.utc)
        else:
            task.completed_at = None

        await session.commit()
        await session.refresh(task)
        return task

    @staticmethod
    async def snooze_task(
        session: AsyncSession,
        task_id: int,
        user_id: int,
        minutes: int
    ) -> Optional[Task]:
        """Menunda pengingat tugas sejumlah menit ke depan."""
        task = await TaskService.get_task(session, task_id, user_id)
        if not task:
            return None

        new_reminder = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        task.snoozed_until = new_reminder
        # Reset flag pengingat terakhir agar bisa membunyikan reminder lagi
        task.reminded_due = False

        await session.commit()
        await session.refresh(task)
        return task

    @staticmethod
    async def delete_task(session: AsyncSession, task_id: int, user_id: int) -> bool:
        """Menghapus tugas."""
        task = await TaskService.get_task(session, task_id, user_id)
        if not task:
            return False

        await session.delete(task)
        await session.commit()
        return True

    @staticmethod
    async def get_due_reminders(session: AsyncSession) -> List[tuple[Task, str]]:
        """
        Memeriksa semua tugas aktif di database yang memenuhi kriteria pengingat:
        - H-1 Hari (24 jam)
        - H-1 Jam (60 menit)
        - H-15 Menit
        - Tepat Waktu (Deadline)
        - Snoozed Trigger
        Mengembalikan tuple: (Task, reminder_stage)
        """
        now_dt = datetime.now(timezone.utc)

        # Query tugas belum selesai yang memiliki due_datetime atau snoozed_until
        stmt = (
            select(Task)
            .options(selectinload(Task.user))
            .where(
                and_(
                    Task.is_completed == False,
                    or_(
                        Task.due_datetime.is_not(None),
                        Task.snoozed_until.is_not(None)
                    )
                )
            )
        )
        result = await session.execute(stmt)
        tasks = result.scalars().all()

        reminders_to_trigger = []

        for task in tasks:
            # Pastikan datetime timezone-aware (SQLite mengembalikan naive datetime)
            snoozed_dt = task.snoozed_until.replace(tzinfo=timezone.utc) if (task.snoozed_until and task.snoozed_until.tzinfo is None) else task.snoozed_until
            due_dt = task.due_datetime.replace(tzinfo=timezone.utc) if (task.due_datetime and task.due_datetime.tzinfo is None) else task.due_datetime

            # 1. Cek Snoozed Reminder
            if snoozed_dt and snoozed_dt <= now_dt:
                reminders_to_trigger.append((task, "SNOOZE"))
                task.snoozed_until = None
                continue

            if not due_dt:
                continue

            time_left = due_dt - now_dt

            # 2. Tepat Waktu (Deadline tercapai atau lewat sampai 15 menit)
            if time_left <= timedelta(seconds=0) and not task.reminded_due:
                task.reminded_due = True
                task.reminded_15m = True
                task.reminded_1h = True
                task.reminded_h1 = True
                reminders_to_trigger.append((task, "DUE"))
            # 3. H-15 Menit
            elif timedelta(seconds=0) < time_left <= timedelta(minutes=15) and not task.reminded_15m:
                task.reminded_15m = True
                task.reminded_1h = True
                task.reminded_h1 = True
                reminders_to_trigger.append((task, "15M"))
            # 4. H-1 Jam
            elif timedelta(minutes=15) < time_left <= timedelta(hours=1) and not task.reminded_1h:
                task.reminded_1h = True
                task.reminded_h1 = True
                reminders_to_trigger.append((task, "1H"))
            # 5. H-1 Hari (24 Jam)
            elif timedelta(hours=1) < time_left <= timedelta(hours=24) and not task.reminded_h1:
                task.reminded_h1 = True
                reminders_to_trigger.append((task, "H1"))

        if reminders_to_trigger:
            await session.commit()

        return reminders_to_trigger

    @staticmethod
    async def get_summary_data(session: AsyncSession, user_id: int) -> dict:
        """Mengumpulkan ringkasan tugas harian untuk rekap pagi atau on-demand."""
        today_tasks = await TaskService.list_tasks(session, user_id, "today")
        overdue_tasks = await TaskService.list_tasks(session, user_id, "overdue")
        upcoming_tasks = await TaskService.list_tasks(session, user_id, "upcoming", limit=5)

        # Hitung tugas dengan prioritas tinggi
        high_priority = [t for t in today_tasks + overdue_tasks + upcoming_tasks if t.priority == "HIGH"]

        return {
            "today": today_tasks,
            "overdue": overdue_tasks,
            "upcoming": upcoming_tasks,
            "high_priority_count": len(high_priority),
            "total_active": len(today_tasks) + len(overdue_tasks) + len(upcoming_tasks)
        }
