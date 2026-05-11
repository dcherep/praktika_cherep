from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models.workshop import Workshop, user_workshop_link
from ..models.user import User
from ..schemas.workshop import WorkshopCreate, WorkshopUpdate, WorkshopRead
from ..dependencies import role_required


router = APIRouter()


@router.get("/public")
def list_workshops_public(db: Session = Depends(get_db)):
    """
    Публичный список мастерских (без авторизации).
    Используется на форме регистрации клиента для выбора филиала.
    """
    from ..models.city import City
    workshops = (
        db.query(Workshop)
        .options(joinedload(Workshop.city))
        .join(City)
        .order_by(City.name, Workshop.name)
        .all()
    )
    return [{
        'id': w.id,
        'name': w.name,
        'city': w.city.name if w.city else None,
        'city_id': w.city_id,
        'address': w.address,
        'phone': w.phone,
    } for w in workshops]


@router.get("/")
def list_workshops(
    db: Session = Depends(get_db),
    user=Depends(role_required("admin", "master")),
):
    """
    Список всех мастерских сети.
    - Admin видит все мастерские
    - Master видит только свою мастерскую
    """
    from ..models.city import City
    if user.role.name == "admin":
        workshops = (
            db.query(Workshop)
            .options(joinedload(Workshop.city))
            .join(City)
            .order_by(City.name, Workshop.name)
            .all()
        )
    else:
        # Master видит только свои мастерские
        workshop_ids = [w.id for w in user.workshops]
        workshops = (
            db.query(Workshop)
            .options(joinedload(Workshop.city))
            .filter(Workshop.id.in_(workshop_ids))
            .all()
        )

    return [{
        'id': w.id,
        'name': w.name,
        'city': w.city.name if w.city else None,
        'city_id': w.city_id,
        'address': w.address,
        'phone': w.phone,
    } for w in workshops]


@router.get("/{workshop_id}", response_model=WorkshopRead)
def get_workshop(
    workshop_id: int,
    db: Session = Depends(get_db),
    user=Depends(role_required("admin", "master")),
):
    """Получить информацию о конкретной мастерской."""
    ws = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not ws:
        raise HTTPException(404, "Мастерская не найдена")
    
    # Master может видеть только свои мастерские
    if user.role.name == "master":
        workshop_ids = [w.id for w in user.workshops]
        if workshop_id not in workshop_ids:
            raise HTTPException(403, "Нет доступа к этой мастерской")
    
    return ws


@router.post("/", response_model=WorkshopRead)
def create_workshop(
    data: WorkshopCreate,
    db: Session = Depends(get_db),
    user=Depends(role_required("admin")),
):
    """Создание новой мастерской (только админ)."""
    ws = Workshop(
        name=data.name,
        city_id=data.city_id,
        address=data.address,
        phone=data.phone
    )
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws


@router.patch("/{workshop_id}", response_model=WorkshopRead)
def update_workshop(
    workshop_id: int,
    data: WorkshopUpdate,
    db: Session = Depends(get_db),
    user=Depends(role_required("admin")),
):
    """Обновление информации о мастерской (только админ)."""
    ws = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not ws:
        raise HTTPException(404, "Мастерская не найдена")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(ws, k, v)
    db.commit()
    db.refresh(ws)
    return ws


@router.delete("/{workshop_id}")
def delete_workshop(
    workshop_id: int,
    db: Session = Depends(get_db),
    user=Depends(role_required("admin")),
):
    """Удаление мастерской (только админ)."""
    ws = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not ws:
        raise HTTPException(404, "Мастерская не найдена")
    db.delete(ws)
    db.commit()
    return {"message": "Мастерская удалена"}


@router.get("/{workshop_id}/users")
def get_workshop_users(
    workshop_id: int,
    db: Session = Depends(get_db),
    user=Depends(role_required("admin", "master")),
):
    """Получить список пользователей в мастерской."""
    ws = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not ws:
        raise HTTPException(404, "Мастерская не найдена")
    
    # Master может видеть только свои мастерские
    if user.role.name == "master":
        workshop_ids = [w.id for w in user.workshops]
        if workshop_id not in workshop_ids:
            raise HTTPException(403, "Нет доступа к этой мастерской")
    
    # Получаем пользователей через связь M2M
    users = db.query(User).join(user_workshop_link).filter(
        user_workshop_link.c.workshop_id == workshop_id
    ).all()
    
    return [
        {
            "id": u.id,
            "name": f"{u.last_name} {u.first_name}",
            "email": u.email,
            "role": u.role.name if u.role else None,
        }
        for u in users
    ]


@router.post("/{workshop_id}/users/{user_id}")
def assign_user_to_workshop(
    workshop_id: int,
    user_id: int,
    role_in_workshop: str = None,
    db: Session = Depends(get_db),
    user=Depends(role_required("admin")),
):
    """Назначить пользователя в мастерскую (только админ)."""
    ws = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not ws:
        raise HTTPException(404, "Мастерская не найдена")
    
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Пользователь не найден")
    
    # Проверяем, не назначен ли уже
    existing = db.query(user_workshop_link).filter(
        user_workshop_link.c.workshop_id == workshop_id,
        user_workshop_link.c.user_id == user_id
    ).first()
    if existing:
        raise HTTPException(400, "Пользователь уже назначен в эту мастерскую")
    
    # Добавляем связь
    db.execute(
        user_workshop_link.insert().values(
            user_id=user_id,
            workshop_id=workshop_id,
            role_in_workshop=role_in_workshop
        )
    )
    db.commit()
    
    return {"message": "Пользователь назначен в мастерскую"}


@router.delete("/{workshop_id}/users/{user_id}")
def remove_user_from_workshop(
    workshop_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(role_required("admin")),
):
    """Удалить пользователя из мастерской (только админ)."""
    db.execute(
        user_workshop_link.delete().where(
            user_workshop_link.c.workshop_id == workshop_id,
            user_workshop_link.c.user_id == user_id
        )
    )
    db.commit()
    return {"message": "Пользователь удалён из мастерской"}

