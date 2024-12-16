# Health check endpoints
from typing import Dict

from fastapi import APIRouter

from app.db.mongodb import db

router = APIRouter(prefix="/health", tags=["health"])


async def check_mongodb() -> Dict[str, str]:
    try:
        # Send a ping to confirm a successful connection
        await db.client.admin.command('ping')
        return {"status": "healthy", "detail": "Connected to MongoDB"}
    except Exception as e:
        return {"status": "unhealthy", "detail": str(e)}


@router.get("")
async def health_check():
    """
    Root health check endpoint.
    Returns basic API status.
    """
    return {
        "status": "healthy",
        "service": "FastAPI Template",
    }


@router.get("/detailed")
async def detailed_health_check():
    """
    Detailed health check endpoint.
    Checks all system components including database connectivity.
    """
    mongodb_status = await check_mongodb()

    # Aggregate overall health status
    is_healthy = all(
        component["status"] == "healthy"
        for component in [mongodb_status]
    )

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "components": {
            "api": {
                "status": "healthy"
            },
            "mongodb": mongodb_status
        }
    }
