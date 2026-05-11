# backend/app/schemas/order_worker.py
"""
Pydantic схемы для связей заказ-техники.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


# ============================================================
# OrderWorker (M2N: заказы ↔ техники)
# ============================================================

class OrderWorkerBase(BaseModel):
    order_id: int
    worker_id: int
    role: Optional[str] = "main"  # main, assistant, observer
    hours_spent: Optional[int] = 0


class OrderWorkerCreate(OrderWorkerBase):
    pass


class OrderWorkerUpdate(BaseModel):
    role: Optional[str] = None
    hours_spent: Optional[int] = None


class OrderWorkerRead(OrderWorkerBase):
    model_config = ConfigDict(from_attributes=True)
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# OrderServiceWorker (M2N: услуги ↔ техники)
# ============================================================

class OrderServiceWorkerBase(BaseModel):
    order_id: int
    service_id: int
    worker_id: int
    hours_spent: Optional[int] = 0


class OrderServiceWorkerCreate(OrderServiceWorkerBase):
    pass


class OrderServiceWorkerUpdate(BaseModel):
    hours_spent: Optional[int] = None


class OrderServiceWorkerRead(OrderServiceWorkerBase):
    model_config = ConfigDict(from_attributes=True)
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
