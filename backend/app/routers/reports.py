# backend/app/routers/reports.py
"""
Роутер отчётов.
GET /reports/personal — Master (заполняет), Admin (просматривает).
GET /reports/finance — только Admin.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models.order import Order
from ..models.payment import Payment
from ..models.user import User, Role
from ..dependencies import role_required

router = APIRouter()


@router.get("/personal")
def personal_report(
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    workshop_id: int | None = Query(None, description="ID мастерской (для фильтрации)"),
    db: Session = Depends(get_db),
    user=Depends(role_required("master", "admin")),
):
    """Отчёт по персоналу: заявки по мастерам."""
    master_role_id = db.query(Role.id).filter(Role.name == "master").scalar()
    if not master_role_id:
        return []
    q = (
        db.query(User.id, User.last_name, User.first_name, func.count(Order.id).label("orders_count"))
        .join(Order, User.id == Order.master_id)
        .filter(User.role_id == master_role_id)
    )
    # Мастер видит только свою мастерскую; админ может указать любую или видеть все.
    effective_workshop_id = workshop_id
    if user.role.name == "master":
        effective_workshop_id = user.workshop_id
    if effective_workshop_id is not None:
        q = q.filter(Order.workshop_id == effective_workshop_id)
    if date_from:
        q = q.filter(Order.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        q = q.filter(Order.created_at <= datetime.fromisoformat(date_to) + timedelta(days=1))
    q = q.group_by(User.id, User.last_name, User.first_name)
    return [{"master_id": r.id, "master": f"{r.last_name} {r.first_name}", "orders_count": r.orders_count} for r in q.all()]


@router.get("/finance")
def finance_report(
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    user=Depends(role_required("admin")),
):
    """Финансовый отчёт: сумма платежей, количество."""
    def _apply_dates(q):
        if date_from:
            q = q.filter(Payment.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            q = q.filter(Payment.created_at <= datetime.fromisoformat(date_to) + timedelta(days=1))
        return q
    q = _apply_dates(db.query(Payment).filter(Payment.status == "stub_ok"))
    total = _apply_dates(db.query(func.sum(Payment.amount)).filter(Payment.status == "stub_ok")).scalar()
    count = q.count()
    return {
        "total_payments": float(total or 0),
        "payments_count": count,
        "currency": "RUB",
    }
