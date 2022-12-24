from fastapi import APIRouter

from .user_controller import user_router
from .auth_controller import auth_router
from .folder_controller import folder_router
from .content_controller import content_router
from .tag_controller import tag_router
from .category_controller import category_router

router = APIRouter()
router.include_router(user_router)
router.include_router(auth_router)
router.include_router(folder_router)
router.include_router(content_router)
router.include_router(tag_router)
router.include_router(category_router)
