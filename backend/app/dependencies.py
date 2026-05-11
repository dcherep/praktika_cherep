# backend/app/dependencies.py
"""
Зависимости FastAPI: JWT-валидация и проверка ролей.
get_current_user — декодирует Bearer-токен, возвращает объект User.
role_required — фабрика зависимости для ограничения доступа по роли.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session, joinedload

from .config import get_settings
from .database import get_db
from .models.user import User

settings = get_settings()
# HTTPBearer — извлекает Bearer-токен из заголовка Authorization. Токен выдаётся при POST /auth/login.
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Основная зависимость аутентификации.
    
    Как работает:
    1. FastAPI извлекает Bearer-токен из заголовка Authorization.
    2. jwt.decode() проверяет подпись и срок действия (exp).
    3. По user_id из payload находим пользователя в БД.
    4. Если пользователь неактивен (is_active=False) — 401.
    5. Возвращаем объект User с загруженной связью role (для проверки прав).
    
    При любой ошибке (неверный токен, истёк срок, пользователь не найден) — HTTP 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учётные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).options(joinedload(User.role)).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise credentials_exception

    return user


def role_required(*allowed_roles: str):
    """
    Фабрика зависимости для проверки роли.
    
    Использование:
        @router.get("/users/")
        def list_users(user = Depends(role_required("admin"))):
            ...
    
    get_current_user вызывается первым (через Depends), затем проверяется role.name.
    Если роль не в списке allowed_roles — HTTP 403 Forbidden.
    """
    def role_checker(user: User = Depends(get_current_user)) -> User:
        role_name = user.role.name if user.role else None
        if role_name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав доступа",
            )
        return user
    return role_checker
