# backend/app/routers/worker_schedules.py
"""
API endpoints для расписания и отсутствий техников.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date

from ..database import get_db
from ..models.user import User
from ..models.worker import Worker
from ..models.worker_schedule import WorkerSchedule, WorkerTimeOff
from ..schemas.worker_schedule import (
    WorkerScheduleCreate, WorkerScheduleUpdate, WorkerScheduleRead,
    WorkerTimeOffCreate, WorkerTimeOffUpdate, WorkerTimeOffRead
)
from ..dependencies import get_current_user, role_required

router = APIRouter(prefix="/worker-schedules", tags=["worker-schedules"])


def _get_user_workshop_ids(db: Session, user: User) -> list:
    """Получить ID мастерских пользователя."""
    from sqlalchemy import text
    result = db.execute(text(f"SELECT workshop_id FROM user_workshop_link WHERE user_id = {user.id}")).fetchall()
    return [r[0] for r in result]


def _can_manage_worker(db: Session, user: User, worker: Worker) -> bool:
    """Проверить права на управление техником."""
    role = user.role.name if user.role else None
    if role == "admin":
        return True
    if role == "master":
        user_ws_ids = _get_user_workshop_ids(db, user)
        return worker.workshop_id in user_ws_ids
    return False


# ============================================================
# WorkerSchedule endpoints
# ============================================================

@router.get("/worker/{worker_id}", response_model=list[WorkerScheduleRead])
def get_worker_schedule(
    worker_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Получить расписание техника.
    - Админ видит всех
    - Мастер видит только техников своих мастерских
    """
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(404, "Техник не найден")
    
    # Проверка прав
    role = user.role.name if user.role else None
    if role == "master":
        user_ws_ids = _get_user_workshop_ids(db, user)
        if worker.workshop_id not in user_ws_ids:
            raise HTTPException(403, "Нет доступа к расписанию этого техника")
    
    q = db.query(WorkerSchedule).filter(WorkerSchedule.worker_id == worker_id)
    
    if date_from:
        q = q.filter(WorkerSchedule.date >= date_from)
    if date_to:
        q = q.filter(WorkerSchedule.date <= date_to)
    
    return q.order_by(WorkerSchedule.date).all()


@router.post("/", response_model=WorkerScheduleRead)
def create_schedule(
    data: WorkerScheduleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(role_required("master", "admin")),
):
    """
    Создать запись в расписании техника.
    """
    worker = db.query(Worker).filter(Worker.id == data.worker_id).first()
    if not worker:
        raise HTTPException(404, "Техник не найден")
    
    # Проверка прав
    if not _can_manage_worker(db, user, worker):
        raise HTTPException(403, "Нет прав на изменение расписания этого техника")
    
    # Проверяем, нет ли уже записи на эту дату
    existing = db.query(WorkerSchedule).filter(
        and_(
            WorkerSchedule.worker_id == data.worker_id,
            WorkerSchedule.date == data.date
        )
    ).first()
    if existing:
        raise HTTPException(400, "Запись на эту дату уже существует")
    
    schedule = WorkerSchedule(**data.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.patch("/{schedule_id}", response_model=WorkerScheduleRead)
def update_schedule(
    schedule_id: int,
    data: WorkerScheduleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(role_required("master", "admin")),
):
    """Обновить запись в расписании."""
    schedule = db.query(WorkerSchedule).filter(WorkerSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(404, "Запись не найдена")
    
    worker = db.query(Worker).filter(Worker.id == schedule.worker_id).first()
    if not _can_manage_worker(db, user, worker):
        raise HTTPException(403, "Нет прав на изменение этого расписания")
    
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(schedule, k, v)
    
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(role_required("master", "admin")),
):
    """Удалить запись из расписания."""
    schedule = db.query(WorkerSchedule).filter(WorkerSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(404, "Запись не найдена")
    
    worker = db.query(Worker).filter(Worker.id == schedule.worker_id).first()
    if not _can_manage_worker(db, user, worker):
        raise HTTPException(403, "Нет прав на удаление этого расписания")
    
    db.delete(schedule)
    db.commit()
    return {"message": "Запись удалена"}


# ============================================================
# WorkerTimeOff endpoints
# ============================================================

@router.get("/time-off/worker/{worker_id}", response_model=list[WorkerTimeOffRead])
def get_worker_time_off(
    worker_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Получить записи об отсутствиях техника."""
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(404, "Техник не найден")
    
    # Проверка прав
    role = user.role.name if user.role else None
    if role == "master":
        user_ws_ids = _get_user_workshop_ids(db, user)
        if worker.workshop_id not in user_ws_ids:
            raise HTTPException(403, "Нет доступа к записям этого техника")
    
    return db.query(WorkerTimeOff).filter(WorkerTimeOff.worker_id == worker_id).all()


@router.post("/time-off", response_model=WorkerTimeOffRead)
def create_time_off(
    data: WorkerTimeOffCreate,
    db: Session = Depends(get_db),
    user: User = Depends(role_required("master", "admin")),
):
    """Создать запись об отсутствии техника."""
    worker = db.query(Worker).filter(Worker.id == data.worker_id).first()
    if not worker:
        raise HTTPException(404, "Техник не найден")
    
    if not _can_manage_worker(db, user, worker):
        raise HTTPException(403, "Нет прав на создание записи")
    
    time_off = WorkerTimeOff(**data.model_dump())
    db.add(time_off)
    db.commit()
    db.refresh(time_off)
    return time_off


@router.delete("/time-off/{time_off_id}")
def delete_time_off(
    time_off_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(role_required("master", "admin")),
):
    """Удалить запись об отсутствии."""
    time_off = db.query(WorkerTimeOff).filter(WorkerTimeOff.id == time_off_id).first()
    if not time_off:
        raise HTTPException(404, "Запись не найдена")
    
    worker = db.query(Worker).filter(Worker.id == time_off.worker_id).first()
    if not _can_manage_worker(db, user, worker):
        raise HTTPException(403, "Нет прав на удаление")
    
    db.delete(time_off)
    db.commit()
    return {"message": "Запись удалена"}
