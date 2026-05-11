# backend/app/config.py
"""
Конфигурация приложения — централизованное хранение настроек.
Все переменные окружения читаются здесь; в продакшене — из .env или Docker environment.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Настройки приложения. Pydantic автоматически читает из env."""
    
    # Строка подключения к PostgreSQL. Формат: postgresql://user:pass@host:port/dbname
    DATABASE_URL: str = "postgresql://postgres:secret@localhost:5432/autoservice"
    
    # Секретный ключ для подписи JWT-токенов. В продакшене — длинная случайная строка.
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Алгоритм шифрования JWT
    ALGORITHM: str = "HS256"
    
    # Время жизни access-токена (секунды). ТЗ: 8 часов.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 * 60
    
    # CORS: разрешённые origins. В продакшене — только домен фронтенда.
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    model_config = ConfigDict(env_file=".env", case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    """Кэшируемый синглтон настроек. Вызов get_settings() всегда возвращает тот же объект."""
    return Settings()
