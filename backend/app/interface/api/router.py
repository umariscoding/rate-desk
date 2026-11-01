from fastapi import APIRouter

from app.interface.api.routers import activity, auth, cases, dorm, health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(cases.router)
api_router.include_router(activity.router)
api_router.include_router(dorm.router)
