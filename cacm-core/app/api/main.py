from fastapi import APIRouter

from app.api.routes import asset, health, tasks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(asset.router)
api_router.include_router(tasks.router)
