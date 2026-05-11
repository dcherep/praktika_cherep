# backend/app/models/city.py
"""
ORM-модель: City (справочник городов).
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class City(Base):
    """
    Справочник городов.

    Связи:
    - workshops → Workshop[] (мастерские в этом городе)

    # ==========================================================================
    # МАСШТАБИРУЕМОСТЬ
    # ==========================================================================
    # - name UNIQUE — исключает дубли городов
    # - region — для расширения (область/край/республика)
    # - В будущем можно добавить: country_id, coordinates, timezone
    # ==========================================================================
    """
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    region = Column(String(100))  # Область/край/республика (опционально)

    # Связи
    workshops = relationship("Workshop", back_populates="city")

    def __repr__(self):
        return f"<City(id={self.id}, name='{self.name}', region='{self.region}')>"
