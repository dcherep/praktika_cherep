# backend/app/routers/payments.py
"""
Роутер платежей — ЗАГЛУШКА.
ТЗ: никакого реального платёжного шлюза. Данные карты НЕ сохраняются.
POST /payments/stub создаёт запись со статусом stub_ok.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.payment import Payment
from ..schemas.payment import PaymentStubIn, PaymentStubOut
from ..dependencies import role_required

router = APIRouter()


@router.post("/stub", response_model=PaymentStubOut)
def stub_payment(
    data: PaymentStubIn,
    db: Session = Depends(get_db),
    user=Depends(role_required("client")),
):
    """
    Заглушка оплаты. Только Client.
    
    Логика (ТЗ):
    - Данные карты намеренно игнорируются, не сохраняются в БД.
    - card_last4 — можно взять из data.card_number[-4:] только для декоративной записи.
    - Создаём Payment с order_id, amount, status='stub_ok'.
    - Возвращаем { success: true }.
    """
    card_last4 = data.card_number[-4:] if data.card_number and len(data.card_number) >= 4 else None
    payment = Payment(
        order_id=data.order_id,
        amount=data.amount,
        card_last4=card_last4,
        status="stub_ok",
    )
    db.add(payment)
    db.commit()
    return PaymentStubOut(success=True, message="Заявка зарегистрирована")
