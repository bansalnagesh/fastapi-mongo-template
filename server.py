# server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import health, users, auth
from app.core.config import settings
from app.db.mongodb import db
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Set up middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add logging middleware
    application.add_middleware(RequestLoggingMiddleware)

    # Add rate limiting middleware (global)
    application.add_middleware(
        RateLimitMiddleware,
        requests_limit=1000,  # 1000 requests per minute globally
        window_size=60
    )

    # Include routers
    application.include_router(health.router, prefix=settings.API_V1_STR)
    application.include_router(users.router, prefix=settings.API_V1_STR)
    application.include_router(auth.router, prefix=settings.API_V1_STR)

    return application


app = create_application()


@app.on_event("startup")
async def startup_db_client():
    await db.connect_to_database()


@app.on_event("shutdown")
async def shutdown_db_client():
    await db.close_database_connection()
