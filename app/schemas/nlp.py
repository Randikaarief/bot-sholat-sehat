from typing import Optional, Literal
from pydantic import BaseModel, Field


class NLPExtractedTask(BaseModel):
    intent: Literal["CREATE_TASK", "LIST_TASKS", "SUMMARY", "COMPLETE_TASK", "DELETE_TASK", "GENERAL_CHAT"] = Field(
        ..., description="Maksud/tujuan utama dari pesan pengguna"
    )
    title: Optional[str] = Field(
        None, description="Nama atau judul tugas yang ringkas dan jelas"
    )
    course_name: Optional[str] = Field(
        None, description="Nama mata kuliah atau topik jika relevan (misal: 'Kecerdasan Buatan', 'Metodologi Penelitian')"
    )
    description: Optional[str] = Field(
        None, description="Keterangan tambahan atau catatan penting"
    )
    due_datetime_iso: Optional[str] = Field(
        None, description="Waktu tenggat dalam format ISO-8601 (misal '2026-10-24T20:00:00+07:00'). Kosong jika tidak ada batas waktu."
    )
    priority: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        "MEDIUM", description="Tingkat prioritas (HIGH jika ada kata 'penting', 'segera', 'urgent')"
    )
    reply_message: str = Field(
        ..., description="Pesan balasan ramah dalam bahasa Indonesia yang menjelaskan apa yang dipahami oleh bot"
    )
