# backend/app/routers/cities.py
"""
API endpoints для справочника городов.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..models.user import User
from ..models.city import City
from ..schemas.city import CityCreate, CityUpdate, CityRead
from ..dependencies import get_current_user, role_required

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("/", response_model=list[CityRead])
def list_cities(
    search: Optional[str] = None,
    region: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Список городов.
    Доступно всем авторизованным пользователям.
    """
    q = db.query(City)
    
    if search:
        q = q.filter(City.name.ilike(f"%{search}%"))
    if region:
        q = q.filter(City.region == region)
    
    return q.order_by(City.name).all()


@router.get("/{city_id}", response_model=CityRead)
def get_city(
    city_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Получить город по ID."""
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(404, "Город не найден")
    return city


@router.post("/", response_model=CityRead)
def create_city(
    data: CityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(role_required("admin")),
):
    """
    Создать город.
    Только для администратора.
    """
    # Проверяем уникальность
    existing = db.query(City).filter(City.name == data.name).first()
    if existing:
        raise HTTPException(400, "Город с таким названием уже существует")
    
    city = City(**data.model_dump())
    db.add(city)
    db.commit()
    db.refresh(city)
    return city


@router.patch("/{city_id}", response_model=CityRead)
def update_city(
    city_id: int,
    data: CityUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(role_required("admin")),
):
    """
    Обновить город.
    Только для администратора.
    """
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(404, "Город не найден")
    
    # Проверяем уникальность нового названия
    if data.name and data.name != city.name:
        existing = db.query(City).filter(City.name == data.name).first()
        if existing:
            raise HTTPException(400, "Город с таким названием уже существует")
    
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(city, k, v)
    
    db.commit()
    db.refresh(city)
    return city


@router.delete("/{city_id}")
def delete_city(
    city_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(role_required("admin")),
):
    """
    Удалить город.
    Только для администратора. Нельзя удалить город, если есть мастерские.
    """
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(404, "Город не найден")
    
    # Проверяем, есть ли мастерские в этом городе
    workshops_count = db.query(text("SELECT COUNT(*) FROM workshops WHERE city_id = :city_id")).params(city_id=city_id).scalar()
    if workshops_count > 0:
        raise HTTPException(400, f"Нельзя удалить город: в нём {workshops_count} мастерских")
    
    db.delete(city)
    db.commit()
    return {"message": "Город удалён"}
