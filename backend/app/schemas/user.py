# backend/app/schemas/user.py
"""Pydantic-схемы для User и Role."""

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from .workshop import WorkshopRead


class RoleRead(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    password: str
    role_id: int
    # Список мастерских, к которым относится пользователь
    workshop_ids: Optional[List[int]] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    email: EmailStr | None = None
    phone: Optional[str] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    workshop_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None


class UserRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    middle_name: Optional[str]
    email: str
    phone: Optional[str]
    role_id: int
    role: Optional[RoleRead] = None
    workshops: List[WorkshopRead] = []
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class UserBrief(BaseModel):
    id: int
    first_name: str
    last_name: str
    model_config = ConfigDict(from_attributes=True)


class UserWorkshopLink(BaseModel):
    """Связь пользователя с мастерской."""
    user_id: int
    workshop_id: int
    role_in_workshop: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
