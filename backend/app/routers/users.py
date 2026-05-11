# backend/app/routers/users.py
"""
Роутер пользователей. Только Admin.
CRUD: список, создание, редактирование, деактивация (is_active=False).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from ..database import get_db
from ..models.user import User, Role
from ..models.workshop import user_workshop_link
from ..schemas.user import UserCreate, UserUpdate, UserRead
from ..routers.auth import get_password_hash
from ..dependencies import role_required

router = APIRouter()


@router.get("/", response_model=list[UserRead])
def list_users(
    role: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(role_required("admin")),
):
    """Список пользователей. Фильтр role=? для выбора мастеров (назначение в заявку)."""
    from ..models.workshop import Workshop
    
    q = db.query(User).options(joinedload(User.role))
    if role:
        role_obj = db.query(Role).filter(Role.name == role).first()
        if role_obj:
            q = q.filter(User.role_id == role_obj.id)
    users = q.all()
    
    # Для каждого пользователя загружаем мастерские через M2M
    result = []
    for u in users:
        # Получаем мастерские через связь
        user_workshops = db.query(Workshop).join(user_workshop_link).filter(
            user_workshop_link.c.user_id == u.id
        ).all()
        u.workshops = user_workshops
        result.append(u)
    
    return result


@router.post("/", response_model=UserRead)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    user=Depends(role_required("admin")),
):
    """Создание пользователя."""
    from ..models.workshop import Workshop
    
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email уже занят")

    role = db.query(Role).filter(Role.id == data.role_id).first()
    if not role:
        raise HTTPException(400, "Роль не найдена")
    
    # Для клиентов и мастеров мастерская обязательна, админ глобальный.
    if role.name in ("client", "master") and (not data.workshop_ids or len(data.workshop_ids) == 0):
        raise HTTPException(400, "Укажите мастерскую для клиента или мастера")

    new_user = User(
        first_name=data.first_name,
        last_name=data.last_name,
        middle_name=data.middle_name,
        email=data.email,
        phone=data.phone,
        password_hash=get_password_hash(data.password),
        role_id=data.role_id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Привязываем к мастерским через M2M
    if data.workshop_ids:
        for wid in data.workshop_ids:
            ws = db.query(Workshop).filter(Workshop.id == wid).first()
            if not ws:
                raise HTTPException(400, f"Мастерская с id={wid} не найдена")
            db.execute(
                user_workshop_link.insert().values(
                    user_id=new_user.id,
                    workshop_id=wid,
                    role_in_workshop=role.name
                )
            )
        db.commit()
    
    # Загружаем мастерские для ответа
    new_user.workshops = db.query(Workshop).join(user_workshop_link).filter(
        user_workshop_link.c.user_id == new_user.id
    ).all()
    
    return new_user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    user=Depends(role_required("admin")),
):
    """Редактирование пользователя."""
    from ..models.workshop import Workshop
    
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Пользователь не найден")
    
    payload = data.model_dump(exclude_unset=True)
    
    # Проверяем смену роли
    if "role_id" in payload:
        role = db.query(Role).filter(Role.id == payload["role_id"]).first()
        if not role:
            raise HTTPException(400, "Роль не найдена")
    
    # Обновляем простые поля
    for k, v in payload.items():
        if k == "password" and v:
            u.password_hash = get_password_hash(v)
        elif k not in ("password", "workshop_ids"):
            setattr(u, k, v)
    
    db.commit()
    
    # Обновляем связь с мастерскими
    if "workshop_ids" in payload and data.workshop_ids is not None:
        # Удаляем старые связи
        db.execute(user_workshop_link.delete().where(user_workshop_link.c.user_id == user_id))
        # Добавляем новые
        for wid in data.workshop_ids:
            ws = db.query(Workshop).filter(Workshop.id == wid).first()
            if not ws:
                raise HTTPException(400, f"Мастерская с id={wid} не найдена")
            db.execute(
                user_workshop_link.insert().values(
                    user_id=user_id,
                    workshop_id=wid,
                    role_in_workshop=u.role.name if u.role else None
                )
            )
        db.commit()
    
    # Загружаем мастерские для ответа
    u.workshops = db.query(Workshop).join(user_workshop_link).filter(
        user_workshop_link.c.user_id == user_id
    ).all()
    
    return u


@router.delete("/{user_id}")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(role_required("admin")),
):
    """Деактивация (is_active=False). ТЗ: не физическое удаление."""
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Пользователь не найден")
    u.is_active = False
    db.commit()
    return {"message": "Пользователь деактивирован"}
