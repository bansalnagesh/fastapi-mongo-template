from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, health, users
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.mongodb import db


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Add CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Set up logging
    # setup_logging()

    # Include routers
    application.include_router(auth.router, prefix=settings.API_V1_STR)
    application.include_router(health.router, prefix=settings.API_V1_STR)
    application.include_router(users.router, prefix=settings.API_V1_STR)

    return application


app = create_application()


@app.on_event("startup")
async def startup_db_client():
    await db.connect_to_database()


@app.on_event("shutdown")
async def shutdown_db_client():
    await db.close_database_connection()
