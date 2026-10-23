import asyncio
from app.core.database import init_db, AsyncSessionLocal
from app.services.task_service import TaskService
from app.services.prayer_service import PrayerService
from app.services.health_service import HealthService


async def test_prayer_service():
    # 1. Tes Pengambilan Jadwal Sholat Kota Surabaya
    timings = await PrayerService.get_prayer_times("Surabaya")
    assert "Fajr" in timings
    assert "Dhuhr" in timings
    assert "Asr" in timings
    assert "Maghrib" in timings
    assert "Isha" in timings
    print(f"Jadwal Sholat Surabaya Berhasil Diambil: {timings}")


async def test_health_service():
    await init_db()
    async with AsyncSessionLocal() as session:
        user = await TaskService.get_or_create_user(session, 123456, "tester", "User Test")
        assert user.city == "Surabaya"

        # Tes catat minum air
        count1, target1 = await HealthService.log_water(session, user)
        assert count1 >= 1

        count2, target2 = await HealthService.log_water(session, user)
        assert count2 == count1 + 1

        # Tes status dashboard
        status = await HealthService.get_health_status(session, user)
        assert status["water_glasses"] == count2
        assert status["sleep_time"] == "22:00"
        print(f"Layanan Kesehatan Berhasil: {status}")


if __name__ == "__main__":
    asyncio.run(test_prayer_service())
    asyncio.run(test_health_service())
    print("Semua tes jadwal sholat & pola hidup sehat 100% SUKSES!")
