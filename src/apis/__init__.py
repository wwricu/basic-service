from fastapi import APIRouter

from apis.auth_controller import auth_router
from apis.category_controller import category_router
from apis.content_controller import content_router
from apis.file_controller import file_router
from apis.folder_controller import folder_router
from apis.tag_controller import tag_router
from apis.user_controller import user_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(category_router)
router.include_router(content_router)
router.include_router(file_router)
router.include_router(folder_router)
router.include_router(tag_router)
router.include_router(user_router)
