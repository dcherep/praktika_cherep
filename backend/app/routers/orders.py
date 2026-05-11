# backend/app/routers/orders.py
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, text

from ..database import get_db
from ..models.user import User
from ..models.order import Order, OrderService
from ..models.service import Service
from ..models.worker import Worker
from ..models.order_worker import OrderWorker, OrderServiceWorker
from ..models.workshop import Workshop, user_workshop_link
from ..schemas.order import OrderCreate, OrderUpdate, OrderRead
from ..dependencies import get_current_user, role_required

router = APIRouter()


@router.get("/")
async def list_orders(
    status: Optional[str] = None,
    workshop_id: Optional[int] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Список заявок с фильтрацией.

    - Client: видит только свои заявки
    - Master: видит заявки своих мастерских
    - Admin: видит все заявки

    Фильтры: status, workshop_id, search (по клиенту или авто), date_from, date_to
    """
    from ..models.city import City
    
    role_name = user.role.name if user.role else None
    q = db.query(Order).options(
        joinedload(Order.client),
        joinedload(Order.master),
        joinedload(Order.workshop).joinedload(Workshop.city),
        joinedload(Order.order_services).joinedload(OrderService.service),
    )

    if role_name == "client":
        q = q.filter(Order.client_id == user.id)
    elif role_name == "master":
        # Мастер видит только заявки своих мастерских
        workshop_ids = [w.id for w in user.workshops]
        q = q.filter(Order.workshop_id.in_(workshop_ids))
    # Admin видит все заявки

    # Дополнительные фильтры
    if status:
        q = q.filter(Order.status == status)
    if workshop_id is not None:
        q = q.filter(Order.workshop_id == workshop_id)

    if search:
        search_pattern = f"%{search}%"
        client_ids = db.query(User.id).filter(
            or_(
                User.last_name.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
            )
        ).subquery()
        q = q.filter(
            or_(
                Order.client_id.in_(client_ids),
                Order.car_model.ilike(search_pattern),
                Order.car_brand.ilike(search_pattern),
            )
        )

    if date_from:
        q = q.filter(Order.created_at >= date_from)
    if date_to:
        q = q.filter(Order.created_at <= date_to)

    order_col = getattr(Order, sort_by, Order.created_at)
    if sort_order == "asc":
        q = q.order_by(order_col.asc())
    else:
        q = q.order_by(order_col.desc())

    orders = q.offset(offset).limit(limit).all()
    
    # Преобразуем всё в простые типы данных (dict без ORM объектов)
    result = []
    for order in orders:
        # Сериализуем order_services
        services_list = []
        for os in order.order_services:
            services_list.append({
                'service_id': os.service_id,
                'service': {
                    'id': os.service.id,
                    'name': os.service.name,
                    'price': float(os.service.price) if os.service.price else 0,
                } if os.service else None,
                'unit_price': float(os.unit_price) if os.unit_price else 0,
                'quantity': os.quantity,
            })
        
        order_dict = {
            'id': order.id,
            'client_id': order.client_id,
            'master_id': order.master_id,
            'car_brand': order.car_brand,
            'car_model': order.car_model,
            'car_year': order.car_year,
            'description': order.description,
            'status': order.status,
            'created_at': str(order.created_at) if order.created_at else None,
            'updated_at': str(order.updated_at) if order.updated_at else None,
            'workshop_id': order.workshop_id,
            'total_amount': float(order.total_amount) if order.total_amount else 0,
            'paid_amount': float(order.paid_amount) if order.paid_amount else 0,
            'order_services': services_list,
        }
        
        # Клиент
        if order.client:
            order_dict['client'] = {
                'id': order.client.id,
                'first_name': order.client.first_name,
                'last_name': order.client.last_name,
                'phone': order.client.phone,
            }
        else:
            order_dict['client'] = None
            
        # Мастер
        if order.master:
            order_dict['master'] = {
                'id': order.master.id,
                'first_name': order.master.first_name,
                'last_name': order.master.last_name,
            }
        else:
            order_dict['master'] = None
        
        # Мастерская
        if order.workshop:
            order_dict['workshop'] = {
                'id': order.workshop.id,
                'name': order.workshop.name,
                'city_id': order.workshop.city_id,
                'address': order.workshop.address,
                'phone': order.workshop.phone,
            }
        else:
            order_dict['workshop'] = None
        
        # Техники назначаются через M2N связь order_workers
        # Для простоты возвращаем пустой список или можно добавить отдельный endpoint
        order_dict['workers'] = []  # Пока пусто, техники назначаются отдельно
            
        result.append(order_dict)
    
    return result


@router.get("/my")
def list_my_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Заявки текущего пользователя (для клиента)."""
    return (
        db.query(Order)
        .filter(Order.client_id == user.id)
        .options(
            joinedload(Order.client),
            joinedload(Order.master),
            joinedload(Order.order_services).joinedload(OrderService.service),
        )
        .order_by(Order.created_at.desc())
        .all()
    )


@router.post("/")
def create_order(data: OrderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Создание новой заявки.

    Клиент может выбрать любую мастерскую.
    Мастер создаёт заявку в своей мастерской.
    """
    role_name = user.role.name if user.role else None

    # Определяем workshop_id
    if role_name == "master":
        # Мастер создаёт заявку в своей мастерской
        from sqlalchemy import select
        stmt = select(user_workshop_link.c.workshop_id).where(user_workshop_link.c.user_id == user.id).limit(1)
        result = db.execute(stmt).scalar()
        if not result:
            raise HTTPException(400, "Мастер не привязан ни к одной мастерской")
        # Мастер может создавать только в своих мастерских
        workshop_id = result
        client_id = user.id
    else:
        # Клиент может выбрать любую мастерскую
        workshop_id = data.workshop_id
        if not workshop_id:
            # Если не указана, берём первую доступную
            first_workshop = db.query(Workshop).first()
            if not first_workshop:
                raise HTTPException(400, "Нет доступных мастерских")
            workshop_id = first_workshop.id
        client_id = user.id

    order = Order(
        client_id=client_id,
        workshop_id=workshop_id,
        car_brand=data.car_brand,
        car_model=data.car_model,
        car_year=data.car_year,
        description=data.description,
        status="new",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Добавляем услуги с ценой на момент заказа
    if data.service_ids and len(data.service_ids) > 0:
        for sid in data.service_ids:
            service = db.query(Service).filter(Service.id == sid).first()
            if service:
                db.add(OrderService(
                    order_id=order.id,
                    service_id=sid,
                    unit_price=service.price,
                    quantity=1
                ))
        db.commit()
        db.refresh(order)

    # Загружаем связанные данные для ответа
    return db.query(Order).filter(Order.id == order.id).first()


@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).options(
        joinedload(Order.client), joinedload(Order.master),
        joinedload(Order.order_services).joinedload(OrderService.service),
    ).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Заявка не найдена")
    role_name = user.role.name if user.role else None
    if role_name == "client" and order.client_id != user.id:
        raise HTTPException(403, "Нет доступа")
    return order


@router.patch("/{order_id}")
def update_order(
    order_id: int, data: OrderUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(role_required("master", "admin")),
):
    """Обновление заявки. Можно изменить все поля + данные клиента."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Заявка не найдена")

    role_name = user.role.name if user.role else None

    # Мастер может изменять только заявки своих мастерских
    if role_name == "master":
        workshop_ids = [w.id for w in user.workshops]
        if order.workshop_id not in workshop_ids:
            raise HTTPException(403, "Нет доступа к заявке другой мастерской")
        # Если master_id не назначен, назначаем текущего мастера
        if order.master_id is None:
            order.master_id = user.id

    # Админ может назначить любого мастера
    if role_name == "admin" and data.master_id is not None:
        order.master_id = data.master_id
        # Если статус new и не указан новый статус, меняем на in_progress
        if order.status == "new" and (data.status is None or data.status == "new"):
            order.status = "in_progress"

    # Обновляем данные клиента (только для admin)
    if role_name == "admin":
        client = db.query(User).filter(User.id == order.client_id).first()
        if client:
            if data.client_first_name is not None:
                client.first_name = data.client_first_name
            if data.client_last_name is not None:
                client.last_name = data.client_last_name
            if data.client_phone is not None:
                client.phone = data.client_phone

    if data.description is not None:
        order.description = data.description

    # Статус можно менять явно через data.status
    if data.status is not None:
        order.status = data.status

    if data.service_ids is not None:
        # Удаляем старые услуги
        db.query(OrderService).filter(OrderService.order_id == order_id).delete(synchronize_session=False)
        # Добавляем новые
        for sid in data.service_ids:
            service = db.query(Service).filter(Service.id == sid).first()
            if service:
                db.add(OrderService(
                    order_id=order_id,
                    service_id=sid,
                    unit_price=service.price,
                    quantity=1
                ))

    db.commit()
    return (
        db.query(Order)
        .options(
            joinedload(Order.client),
            joinedload(Order.master),
            joinedload(Order.order_services).joinedload(OrderService.service),
        )
        .filter(Order.id == order_id)
        .first()
    )


@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(role_required("master", "admin")),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Заявка не найдена")

    role_name = user.role.name if user.role else None
    
    # Мастер может удалять только заявки своих мастерских и только в статусах new/in_progress
    if role_name == "master":
        workshop_ids = [w.id for w in user.workshops]
        if order.workshop_id not in workshop_ids:
            raise HTTPException(403, "Нет доступа к заявке другой мастерской")
        if order.status not in ("new", "in_progress"):
            raise HTTPException(400, "Мастер может удалять только заявки в статусах 'Новая' или 'В работе'")
    
    # Админ может удалять заявки в любом статусе
    db.delete(order)
    db.commit()
    return {"message": "Заявка удалена"}


# ============================================================
# Order Workers (M2N связь заказы ↔ техники)
# ============================================================

@router.get("/{order_id}/workers", response_model=list[dict])
def get_order_workers(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Получить всех техников, назначенных на заявку."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Заявка не найдена")
    
    # Проверка прав
    role = user.role.name if user.role else None
    if role == "client" and order.client_id != user.id:
        raise HTTPException(403, "Нет доступа")
    if role == "master":
        workshop_ids = [w.id for w in user.workshops]
        if order.workshop_id not in workshop_ids:
            raise HTTPException(403, "Нет доступа")
    
    # Получаем назначения
    assignments = db.query(OrderWorker).filter(OrderWorker.order_id == order_id).all()
    
    result = []
    for aw in assignments:
        worker = db.query(Worker).filter(Worker.id == aw.worker_id).first()
        result.append({
            "worker_id": worker.id,
            "worker_name": f"{worker.first_name} {worker.last_name}",
            "role": aw.role,
            "hours_spent": aw.hours_spent,
        })
    
    return result


@router.post("/{order_id}/workers", response_model=dict)
def assign_worker_to_order(
    order_id: int,
    worker_id: int,
    role: str = "main",
    hours_spent: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(role_required("master", "admin")),
):
    """
    Назначить техника на заявку.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Заявка не найдена")
    
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(404, "Техник не найден")
    
    # Проверка: техник должен быть из той же мастерской
    if worker.workshop_id != order.workshop_id:
        raise HTTPException(400, "Техник должен быть из той же мастерской")
    
    # Проверка прав
    role_name = user.role.name if user.role else None
    if role_name == "master":
        workshop_ids = [w.id for w in user.workshops]
        if order.workshop_id not in workshop_ids:
            raise HTTPException(403, "Нет доступа")
    
    # Проверяем, не назначен ли уже
    existing = db.query(OrderWorker).filter(
        and_(OrderWorker.order_id == order_id, OrderWorker.worker_id == worker_id)
    ).first()
    if existing:
        raise HTTPException(400, "Техник уже назначен на эту заявку")
    
    # Создаём назначение
    assignment = OrderWorker(
        order_id=order_id,
        worker_id=worker_id,
        role=role,
        hours_spent=hours_spent,
    )
    db.add(assignment)
    db.commit()
    
    return {"message": "Техник назначен", "worker_id": worker_id, "role": role}


@router.delete("/{order_id}/workers/{worker_id}")
def remove_worker_from_order(
    order_id: int,
    worker_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(role_required("master", "admin")),
):
    """Удалить техника из заявки."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Заявка не найдена")
    
    # Проверка прав
    role_name = user.role.name if user.role else None
    if role_name == "master":
        workshop_ids = [w.id for w in user.workshops]
        if order.workshop_id not in workshop_ids:
            raise HTTPException(403, "Нет доступа")
    
    assignment = db.query(OrderWorker).filter(
        and_(OrderWorker.order_id == order_id, OrderWorker.worker_id == worker_id)
    ).first()
    if not assignment:
        raise HTTPException(404, "Техник не назначен на эту заявку")
    
    db.delete(assignment)
    db.commit()
    return {"message": "Техник удалён из заявки"}


# ============================================================
# Order Service Workers (техники на услугах)
# ============================================================

@router.get("/{order_id}/service-workers", response_model=list[dict])
def get_order_service_workers(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Получить техников, назначенных на услуги заявки."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Заявка не найдена")
    
    # Проверка прав
    role = user.role.name if user.role else None
    if role == "client" and order.client_id != user.id:
        raise HTTPException(403, "Нет доступа")
    
    assignments = db.query(OrderServiceWorker).filter(
        OrderServiceWorker.order_id == order_id
    ).all()
    
    result = []
    for aw in assignments:
        service = db.query(Service).filter(Service.id == aw.service_id).first()
        worker = db.query(Worker).filter(Worker.id == aw.worker_id).first()
        result.append({
            "service_id": service.id,
            "service_name": service.name,
            "worker_id": worker.id,
            "worker_name": f"{worker.first_name} {worker.last_name}",
            "hours_spent": aw.hours_spent,
        })
    
    return result


@router.post("/{order_id}/service-workers", response_model=dict)
def assign_worker_to_service(
    order_id: int,
    service_id: int,
    worker_id: int,
    hours_spent: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(role_required("master", "admin")),
):
    """Назначить техника на услугу."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Заявка не найдена")
    
    # Проверка: услуга должна быть в заявке
    order_service = db.query(OrderService).filter(
        and_(OrderService.order_id == order_id, OrderService.service_id == service_id)
    ).first()
    if not order_service:
        raise HTTPException(400, "Услуга не найдена в заявке")
    
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(404, "Техник не найден")
    
    # Проверка: техник из той же мастерской
    if worker.workshop_id != order.workshop_id:
        raise HTTPException(400, "Техник должен быть из той же мастерской")
    
    # Проверка прав
    role_name = user.role.name if user.role else None
    if role_name == "master":
        workshop_ids = [w.id for w in user.workshops]
        if order.workshop_id not in workshop_ids:
            raise HTTPException(403, "Нет доступа")
    
    # Проверяем существующее назначение
    existing = db.query(OrderServiceWorker).filter(
        and_(
            OrderServiceWorker.order_id == order_id,
            OrderServiceWorker.service_id == service_id,
            OrderServiceWorker.worker_id == worker_id,
        )
    ).first()
    if existing:
        raise HTTPException(400, "Техник уже назначен на эту услугу")
    
    assignment = OrderServiceWorker(
        order_id=order_id,
        service_id=service_id,
        worker_id=worker_id,
        hours_spent=hours_spent,
    )
    db.add(assignment)
    db.commit()
    
    return {"message": "Техник назначен на услугу"}


@router.delete("/{order_id}/service-workers/{worker_id}/{service_id}")
def remove_worker_from_service(
    order_id: int,
    worker_id: int,
    service_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(role_required("master", "admin")),
):
    """Удалить техника из услуги."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Заявка не найдена")
    
    # Проверка прав
    role_name = user.role.name if user.role else None
    if role_name == "master":
        workshop_ids = [w.id for w in user.workshops]
        if order.workshop_id not in workshop_ids:
            raise HTTPException(403, "Нет доступа")
    
    assignment = db.query(OrderServiceWorker).filter(
        and_(
            OrderServiceWorker.order_id == order_id,
            OrderServiceWorker.service_id == service_id,
            OrderServiceWorker.worker_id == worker_id,
        )
    ).first()
    if not assignment:
        raise HTTPException(404, "Назначение не найдено")
    
    db.delete(assignment)
    db.commit()
    return {"message": "Техник удалён из услуги"}
