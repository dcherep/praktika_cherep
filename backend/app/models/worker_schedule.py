# backend/app/models/worker_schedule.py
"""
ORM-модели: WorkerSchedule и WorkerTimeOff (расписание и отсутствия техников).
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..database import Base


class ShiftType(enum.Enum):
    """Типы смен."""
    morning = "morning"      # Утренняя (например, 08:00-16:00)
    evening = "evening"      # Вечерняя (например, 16:00-00:00)
    night = "night"          # Ночная (например, 00:00-08:00)
    full = "full"            # Полный день
    half = "half"            # Половина дня


class TimeOffReason(enum.Enum):
    """Причины отсутствия."""
    vacation = "vacation"    # Отпуск
    sick = "sick"            # Больничный
    other = "other"          # Другое


class WorkerSchedule(Base):
    """
    График работы техника.

    Связи:
    - worker_id -> Worker (техник)

    # ==========================================================================
    # МАСШТАБИРУЕМОСТЬ
    # ==========================================================================
    # - Позволяет планировать смены техников
    # - is_working=False — выходной/праздник
    # - В будущем можно добавить: start_time, end_time, break_time
    # ==========================================================================
    """
    __tablename__ = "worker_schedules"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    shift_type = Column(String(20), default="full")  # morning/evening/night/full/half
    hours = Column(Integer, default=8)
    is_working = Column(Boolean, default=True)
    comment = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Связи
    worker = relationship("Worker", back_populates="schedules")

    def __repr__(self):
        return f"<WorkerSchedule(id={self.id}, worker_id={self.worker_id}, date={self.date}, shift={self.shift_type})>"


class WorkerTimeOff(Base):
    """
    Отсутствие техника (отпуск/больничный).

    Связи:
    - worker_id -> Worker (техник)

    # ==========================================================================
    # МАСШТАБИРУЕМОСТЬ
    # ==========================================================================
    # - Позволяет отслеживать периоды отсутствия
    # - В будущем можно добавить: status (approved/rejected), approved_by
    # ==========================================================================
    """
    __tablename__ = "worker_time_off"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String(50), nullable=False)  # vacation/sick/other
    comment = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Связи
    worker = relationship("Worker", back_populates="time_off")

    def __repr__(self):
        return f"<WorkerTimeOff(id={self.id}, worker_id={self.worker_id}, {self.start_date} - {self.end_date}, {self.reason})>"
