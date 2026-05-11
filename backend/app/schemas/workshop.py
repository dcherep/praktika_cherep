from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class WorkshopBase(BaseModel):
    name: str
    city_id: Optional[int] = None  # ID города
    address: Optional[str] = None
    phone: Optional[str] = None


class WorkshopCreate(WorkshopBase):
    pass


class WorkshopUpdate(BaseModel):
    name: Optional[str] = None
    city_id: Optional[int] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class WorkshopRead(WorkshopBase):
    id: int
    # city удалён — используется только city_id для масштабируемости
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WorkshopWithUsers(WorkshopRead):
    """Мастерская со списком пользователей."""
    users: List[dict] = []
    model_config = {"from_attributes": True}

