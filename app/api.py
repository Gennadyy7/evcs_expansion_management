from fastapi import APIRouter

from app.features.core.router import router as core_router
from app.features.reference.router import router as reference_router

api_router = APIRouter()
api_router.include_router(reference_router)
api_router.include_router(core_router)
