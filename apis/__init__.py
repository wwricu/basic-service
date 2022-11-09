from fastapi import APIRouter

from .user_controller import user_router

router = APIRouter()
router.include_router(user_router)
