from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    course_name: Optional[str] = None
    due_datetime: Optional[datetime] = None
    priority: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"


class TaskCreate(TaskBase):
    source: str = "MANUAL"
    external_uid: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    course_name: Optional[str] = None
    due_datetime: Optional[datetime] = None
    priority: Optional[Literal["LOW", "MEDIUM", "HIGH"]] = None
    is_completed: Optional[bool] = None


class TaskOut(TaskBase):
    id: int
    user_id: int
    source: str
    external_uid: Optional[str] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    snoozed_until: Optional[datetime] = None

    class Config:
        from_attributes = True
