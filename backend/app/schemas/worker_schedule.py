# backend/app/schemas/worker_schedule.py
"""
Pydantic схемы для расписания и отсутствий техников.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime, date


# ============================================================
# WorkerSchedule
# ============================================================

class WorkerScheduleBase(BaseModel):
    worker_id: int
    date: date
    shift_type: Optional[str] = "full"  # full, morning, evening, night, half
    hours: Optional[int] = 8
    is_working: Optional[bool] = True
    comment: Optional[str] = None


class WorkerScheduleCreate(WorkerScheduleBase):
    pass


class WorkerScheduleUpdate(BaseModel):
    shift_type: Optional[str] = None
    hours: Optional[int] = None
    is_working: Optional[bool] = None
    comment: Optional[str] = None


class WorkerScheduleRead(WorkerScheduleBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# WorkerTimeOff
# ============================================================

class WorkerTimeOffBase(BaseModel):
    worker_id: int
    start_date: date
    end_date: date
    reason: str  # vacation, sick, other
    comment: Optional[str] = None


class WorkerTimeOffCreate(WorkerTimeOffBase):
    pass


class WorkerTimeOffUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reason: Optional[str] = None
    comment: Optional[str] = None


class WorkerTimeOffRead(WorkerTimeOffBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
