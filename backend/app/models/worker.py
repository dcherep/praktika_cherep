from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Worker(Base):
    """
    Работник (исполнитель) внутри мастерской.

    Отличается от пользователя:
    - Пользователь = роль в системе (клиент / мастер / админ).
    - Worker = конкретный сотрудник, которого мастер назначает на заявку.

    # ==========================================================================
    # МАСШТАБИРУЕМОСТЬ
    # ==========================================================================
    # - updated_at — отслеживание изменений
    # - is_active — мягкое отключение (архивные сотрудники)
    # - В будущем можно добавить: user_id (если техник получает доступ к системе)
    #   phone, email, hire_date, certification_level
    # ==========================================================================
    """

    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    position = Column(String(100), nullable=True)
    workshop_id = Column(Integer, ForeignKey("workshops.id", ondelete="CASCADE"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Связи
    workshop = relationship("Workshop", back_populates="workers")

    # Заявки, на которые назначен работник (M2N через order_workers)
    orders = relationship("OrderWorker", back_populates="worker")

    # Услуги, которые выполнял работник (M2N через order_service_workers)
    service_assignments = relationship("OrderServiceWorker", back_populates="worker")

    # График работы
    schedules = relationship("WorkerSchedule", back_populates="worker", cascade="all, delete-orphan")

    # Отпуска/больничные
    time_off = relationship("WorkerTimeOff", back_populates="worker", cascade="all, delete-orphan")

