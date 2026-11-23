from fastapi import APIRouter

from app.features.reference.router import router as reference_router

api_router = APIRouter()
api_router.include_router(reference_router)
