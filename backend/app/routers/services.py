# backend/app/routers/services.py
"""
Роутер услуг. Все видят список. Создание/редактирование — только Admin.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.service import Service
from ..schemas.service import ServiceCreate, ServiceUpdate, ServiceRead
from ..dependencies import get_current_user, role_required

router = APIRouter()


@router.get("/", response_model=list[ServiceRead])
def list_services(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Список услуг. Доступ всем авторизованным."""
    return db.query(Service).all()


@router.post("/", response_model=ServiceRead)
def create_service(
    data: ServiceCreate,
    db: Session = Depends(get_db),
    user=Depends(role_required("admin")),
):
    """Создание услуги. Только Admin."""
    svc = Service(name=data.name, price=data.price)
    db.add(svc)
    db.commit()
    db.refresh(svc)
    return svc


@router.patch("/{service_id}", response_model=ServiceRead)
def update_service(
    service_id: int,
    data: ServiceUpdate,
    db: Session = Depends(get_db),
    user=Depends(role_required("admin")),
):
    """Редактирование услуги. Только Admin."""
    svc = db.query(Service).filter(Service.id == service_id).first()
    if not svc:
        raise HTTPException(404, "Услуга не найдена")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(svc, k, v)
    db.commit()
    db.refresh(svc)
    return svc
