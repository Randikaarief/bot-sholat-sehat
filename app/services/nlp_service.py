import json
import logging
from datetime import datetime
from typing import Optional
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.timezone import now_local, format_dt
from app.schemas.nlp import NLPExtractedTask

logger = logging.getLogger(__name__)


class NLPService:
    @staticmethod
    def get_client() -> Optional[genai.Client]:
        """Inisialisasi klien Gemini SDK jika API Key tersedia."""
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY belum dikonfigurasi di file .env")
            return None
        return genai.Client(api_key=settings.GEMINI_API_KEY)

    @staticmethod
    async def extract_from_text(text: str, user_tz_str: str = "Asia/Jakarta") -> NLPExtractedTask:
        """
        Mengekstrak informasi tugas, tenggat waktu, dan intent dari teks percakapan santai.
        """
        client = NLPService.get_client()
        current_time = now_local(user_tz_str)
        formatted_current = format_dt(current_time, user_tz_str, include_time=True)

        if not client:
            # Fallback jika belum pasang API Key Gemini
            return NLPExtractedTask(
                intent="CREATE_TASK",
                title=text[:100],
                course_name=None,
                description=None,
                due_datetime_iso=None,
                priority="MEDIUM",
                reply_message=f"Catatan: Gemini API Key belum disetel. Tugas '{text[:50]}' disimpan secara manual tanpa ekstraksi waktu otomatis."
            )

        prompt = f"""
Anda adalah asisten pribadi cerdas untuk manajemen tugas dan pengingat harian mahasiswa/profesional.
Tugas Anda adalah memahami pesan pengguna dalam bahasa Indonesia (sering menggunakan bahasa gaul, santai, atau singkatan) dan mengekstrak entitas tugas secara terstruktur.

WAKTU SAAT INI (ZONA WAKTU LOKAL):
{formatted_current} (ISO: {current_time.isoformat()})

ATURAN EKSTRAKSI WAKTU:
1. Jika pengguna menyebut waktu relatif:
   - "nanti malam" -> hari ini pukul 19:30 atau 20:00
   - "nanti sore" -> hari ini pukul 16:00
   - "nanti siang" -> hari ini pukul 12:30
   - "besok jam X" -> (hari ini + 1 hari) pukul X
   - "lusa jam X" -> (hari ini + 2 hari) pukul X
   - "hari senin/selasa/..." -> cari hari tersebut yang paling dekat di masa mendatang
   - "setengah jam lagi" / "1 jam lagi" -> waktu saat ini ditambah durasi tersebut
2. Konversi due_datetime_iso ke format ISO 8601 lengkap dengan offset zona waktu (+07:00 untuk WIB).
3. Buat judul tugas yang bersih tanpa kata pengantar seperti "ingatkan saya", "tolong catat", "ada tugas", dsb.
4. Jika ada indikasi mendesak, penting, kuis, atau ujian, set priority = "HIGH".
5. Berikan 'reply_message' dalam bahasa Indonesia yang ramah, sopan, dan mengonfirmasi tugas yang berhasil ditangkap.

Pesan Pengguna:
"{text}"
"""

        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=NLPExtractedTask,
                    temperature=0.2,
                )
            )

            # Parse hasil JSON dari Gemini
            result_data = json.loads(response.text)
            return NLPExtractedTask(**result_data)
        except Exception as e:
            logger.error(f"Error saat memanggil Gemini API: {e}")
            return NLPExtractedTask(
                intent="CREATE_TASK",
                title=text[:100],
                course_name=None,
                description=None,
                due_datetime_iso=None,
                priority="MEDIUM",
                reply_message=f"Tugas dicatat: '{text[:50]}'. (Ekstraksi otomatis mengalami kendala teknis: {e})"
            )

    @staticmethod
    async def extract_from_image(
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        user_tz_str: str = "Asia/Jakarta"
    ) -> NLPExtractedTask:
        """
        Mengekstrak informasi tugas dari gambar tangkapan layar (screenshot LMS Vinesa, grup WA, atau catatan).
        """
        client = NLPService.get_client()
        current_time = now_local(user_tz_str)
        formatted_current = format_dt(current_time, user_tz_str, include_time=True)

        if not client:
            return NLPExtractedTask(
                intent="CREATE_TASK",
                title="Tugas dari Gambar",
                course_name=None,
                description=None,
                due_datetime_iso=None,
                priority="MEDIUM",
                reply_message="API Key Gemini belum diatur di .env sehingga tidak dapat menganalisis gambar screenshot."
            )

        prompt = f"""
Perhatikan gambar tangkapan layar ini secara teliti. Gambar ini kemungkinan merupakan screenshot dari LMS Vinesa Moodle UNESA, Google Classroom, atau pengumuman tugas di grup chat.

Tugas Anda:
1. Temukan nama mata kuliah / kursus jika ada.
2. Temukan nama atau judul tugas / kuis / UTS / UAS.
3. Temukan tanggal & jam tenggat waktu (due date / cut-off date).
4. Buat rangkuman catatan penting dari instruksi tugas tersebut.
5. Hitung due_datetime_iso dengan offset +07:00 (WIB) berdasarkan waktu referensi saat ini:
   WAKTU SAAT INI: {formatted_current} (ISO: {current_time.isoformat()}).
"""

        try:
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )

            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[image_part, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=NLPExtractedTask,
                    temperature=0.1,
                )
            )

            result_data = json.loads(response.text)
            return NLPExtractedTask(**result_data)
        except Exception as e:
            logger.error(f"Error saat memproses gambar dengan Gemini: {e}")
            return NLPExtractedTask(
                intent="CREATE_TASK",
                title="Tugas dari Gambar (Gagal ekstrak otomatis)",
                course_name=None,
                description=f"Error pemrosesan gambar: {e}",
                due_datetime_iso=None,
                priority="MEDIUM",
                reply_message="Maaf, saya tidak dapat membaca informasi tugas dari gambar ini secara jelas."
            )
