# backend/app/main.py
"""
Точка входа FastAPI-приложения.
Подключает роутеры, настраивает CORS и глобальные обработчики.
"""

import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import auth, orders, users, services, payments, workshops, workers, cities, worker_schedules

settings = get_settings()

# Настраиваем логгер (будет использовать тот же поток, что и uvicorn)
logger = logging.getLogger("uvicorn")

async def log_requests(request: Request, call_next):
    """Middleware для логирования запросов в стиле Django runserver."""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}ms"
    )
    return response

app = FastAPI(
    title="API автосервиса",
    description="REST API для системы управления автосервисом (ТЗ v3.1 Scalable)",
    version="3.1.0",
)

# Регистрируем middleware логирования (должен быть до CORS, чтобы видеть все запросы)
app.middleware("http")(log_requests)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Авторизация"])
app.include_router(orders.router, prefix="/orders", tags=["Заявки"])
app.include_router(users.router, prefix="/users", tags=["Пользователи"])
app.include_router(services.router, prefix="/services", tags=["Услуги"])
app.include_router(payments.router, prefix="/payments", tags=["Платежи"])
app.include_router(workshops.router, prefix="/workshops", tags=["Мастерские"])
app.include_router(workers.router, prefix="/workers", tags=["Работники"])
app.include_router(cities.router, tags=["Города"])
app.include_router(worker_schedules.router, tags=["Расписание техников"])


@app.get("/")
def root():
    return {"message": "API автосервиса", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)