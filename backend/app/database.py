# backend/app/database.py
"""
Подключение к PostgreSQL через SQLAlchemy 2.0.
Создаём сессию БД через dependency get_db(); она автоматически закрывается после запроса.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import get_settings

settings = get_settings()

# Engine — пул соединений к БД. Один engine на всё приложение.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Проверяет соединение перед использованием
    echo=True,  # True — логировать SQL-запросы (для отладки)
)

# SessionLocal — фабрика сессий. Каждый запрос получает свою сессию.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base — базовый класс для всех ORM-моделей (таблиц)
Base = declarative_base()


def get_db():
    """
    Dependency для FastAPI. Вызывает yield, отдаёт сессию в эндпоинт,
    после ответа — закрывает сессию (finally).
    Использование: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
