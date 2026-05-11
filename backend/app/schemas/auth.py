# backend/app/schemas/auth.py
"""Pydantic-схемы для авторизации."""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    token: str
    user: dict  # { id, name, role }
    token_type: str = "bearer"


class ClientRegisterRequest(BaseModel):
    """Запрос на самостоятельную регистрацию клиента."""

    first_name: str
    last_name: str
    middle_name: str | None = None
    email: EmailStr
    phone: str | None = None
    password: str
    workshop_id: int  # Мастерская (город/филиал), в которую будут попадать заявки клиента
