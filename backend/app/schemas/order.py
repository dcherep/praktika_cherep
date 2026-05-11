from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from .service import ServiceRead
from .user import UserBrief
from .workshop import WorkshopRead
from .worker import WorkerRead


class OrderServiceRead(BaseModel):
    service_id: int
    service: Optional[ServiceRead] = None
    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    car_brand: str = Field(..., description="Марка автомобиля")
    car_model: str = Field(..., description="Модель автомобиля")
    car_year: int = Field(..., description="Год выпуска")
    description: Optional[str] = Field(None, description="Описание проблемы")
    service_ids: List[int] = Field(default_factory=list, description="Список ID услуг")
    workshop_id: Optional[int] = Field(None, description="ID мастерской (если не указана, выбирается первая)")


class OrderUpdate(BaseModel):
    master_id: Optional[int] = None
    # worker_id удалён — используем M2N связь через order_workers
    description: Optional[str] = None
    status: Optional[str] = Field(None, description="Статус: new, in_progress, done")
    service_ids: Optional[List[int]] = None
    workshop_id: Optional[int] = None
    # Данные клиента для редактирования
    client_first_name: Optional[str] = None
    client_last_name: Optional[str] = None
    client_phone: Optional[str] = None


class OrderRead(BaseModel):
    id: int
    client_id: int
    master_id: Optional[int]
    car_brand: str
    car_model: str
    car_year: int
    description: Optional[str]
    status: str = Field(..., description="Статус: new, in_progress, done")
    created_at: datetime
    updated_at: datetime
    workshop_id: int
    # workshop удалён — вызывает проблемы с city
    # worker удалён — используем M2N связь через order_workers
    client: Optional[UserBrief] = None
    master: Optional[UserBrief] = None
    order_services: List[OrderServiceRead] = []
    model_config = {"from_attributes": True}
