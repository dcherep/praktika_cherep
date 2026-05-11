from pydantic import BaseModel


class WorkerBase(BaseModel):
  first_name: str
  last_name: str
  position: str | None = None


class WorkerCreate(WorkerBase):
  workshop_id: int | None = None


class WorkerUpdate(BaseModel):
  first_name: str | None = None
  last_name: str | None = None
  position: str | None = None
  is_active: bool | None = None


class WorkerRead(WorkerBase):
  id: int
  workshop_id: int
  is_active: bool
  # вычисляемое поле: назначен хотя бы на одну незавершённую заявку (в роутере workers; здесь по умолчанию False)
  is_assigned: bool = False
  model_config = {"from_attributes": True}

