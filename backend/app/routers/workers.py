from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..models.worker import Worker
from ..models.order import Order
from ..schemas.worker import WorkerCreate, WorkerUpdate, WorkerRead
from ..dependencies import get_current_user, role_required


router = APIRouter()


def _get_user_workshop_ids(db: Session, user) -> list:
    """Получить ID мастерских пользователя через M2M связь."""
    result = db.execute(text(f"SELECT workshop_id FROM user_workshop_link WHERE user_id = {user.id}")).fetchall()
    return [r[0] for r in result]


def _can_manage_worker(db: Session, user, worker: Worker) -> bool:
    # Админ может управлять всеми, мастер — только в своей мастерской.
    role = user.role.name if user.role else None
    if role == "admin":
        return True
    if role == "master":
        user_ws_ids = _get_user_workshop_ids(db, user)
        return worker.workshop_id in user_ws_ids
    return False


@router.get("/")
def list_workers(
    db: Session = Depends(get_db),
    user=Depends(role_required("master", "admin")),
):
    """
    Список работников.
    - Мастер видит только работников своей мастерской.
    - Админ видит всех.
    """
    from ..models.user import User
    
    q = db.query(Worker)
    role = user.role.name if user.role else None
    if role == "master":
        user_ws_ids = _get_user_workshop_ids(db, user)
        q = q.filter(Worker.workshop_id.in_(user_ws_ids))

    workers = q.order_by(Worker.workshop_id, Worker.last_name, Worker.first_name).all()

    # Возвращаем простых dict без response_model
    result = []
    for w in workers:
        result.append({
            "id": w.id,
            "first_name": w.first_name,
            "last_name": w.last_name,
            "position": w.position,
            "workshop_id": w.workshop_id,
            "is_active": w.is_active,
            "is_assigned": False,  # Пока заглушка
        })

    return result


@router.get("/workshop/{workshop_id}")
def list_workers_by_workshop(
    workshop_id: int,
    db: Session = Depends(get_db),
    user=Depends(role_required("master", "admin")),
):
    """
    Список работников конкретной мастерской.
    Используется при назначении техника на заявку.
    - Админ может смотреть работников любой мастерской.
    - Мастер может смотреть только работников своей мастерской.
    """
    # Проверяем доступ
    role = user.role.name if user.role else None
    if role == "master":
        user_ws_ids = _get_user_workshop_ids(db, user)
        if workshop_id not in user_ws_ids:
            raise HTTPException(403, "Нет доступа к работникам этой мастерской")

    # Получаем работников
    workers = (
        db.query(Worker)
        .filter(Worker.workshop_id == workshop_id)
        .order_by(Worker.last_name, Worker.first_name)
        .all()
    )

    # Возвращаем простых dict
    result = []
    for w in workers:
        result.append({
            "id": w.id,
            "first_name": w.first_name,
            "last_name": w.last_name,
            "position": w.position,
            "workshop_id": w.workshop_id,
            "is_active": w.is_active,
            "is_assigned": False,  # Пока заглушка
        })

    return result


@router.post("/", response_model=WorkerRead)
def create_worker(
    data: WorkerCreate,
    db: Session = Depends(get_db),
    user=Depends(role_required("master", "admin")),
):
    """
    Создание работника.
    - Для мастера workshop_id всегда совпадает с его мастерской.
    - Админ может указать любую мастерскую.
    """
    role = user.role.name if user.role else None
    workshop_id = data.workshop_id
    if role == "master":
        if not user.workshops:
            raise HTTPException(400, "Мастер не привязан ни к одной мастерской")
        workshop_id = user.workshops[0].id
    if workshop_id is None:
        raise HTTPException(400, "Укажите мастерскую для работника")

    worker = Worker(
        first_name=data.first_name,
        last_name=data.last_name,
        position=data.position,
        workshop_id=workshop_id,
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)

    return WorkerRead(
        id=worker.id,
        first_name=worker.first_name,
        last_name=worker.last_name,
        position=worker.position,
        workshop_id=worker.workshop_id,
        is_active=worker.is_active,
        is_assigned=False,
    )


@router.patch("/{worker_id}", response_model=WorkerRead)
def update_worker(
    worker_id: int,
    data: WorkerUpdate,
    db: Session = Depends(get_db),
    user=Depends(role_required("master", "admin")),
):
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(404, "Работник не найден")
    if not _can_manage_worker(db, user, worker):
        raise HTTPException(403, "Нет прав на изменение этого работника")

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(worker, k, v)
    db.commit()
    db.refresh(worker)

    # пересчитываем флаг назначения (через M2N order_workers)
    from ..models.order_worker import OrderWorker
    assigned = (
        db.query(OrderWorker)
        .join(Order, OrderWorker.order_id == Order.id)
        .filter(OrderWorker.worker_id == worker.id, Order.status != "done")
        .first()
        is not None
    )

    return WorkerRead(
        id=worker.id,
        first_name=worker.first_name,
        last_name=worker.last_name,
        position=worker.position,
        workshop_id=worker.workshop_id,
        is_active=worker.is_active,
        is_assigned=assigned,
    )

