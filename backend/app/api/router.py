from fastapi import APIRouter

from app.api.views import router as views_router

api_router = APIRouter()
api_router.include_router(views_router)

