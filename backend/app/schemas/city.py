# backend/app/schemas/city.py
"""
Pydantic схемы для городов.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class CityBase(BaseModel):
    name: str
    region: Optional[str] = None


class CityCreate(CityBase):
    pass


class CityUpdate(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None


class CityRead(CityBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
