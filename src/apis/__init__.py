from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from .auth_controller import auth_router
from .category_controller import category_router
from .content_controller import content_router
from .file_controller import file_router
from .folder_controller import folder_router
from .tag_controller import tag_router
from .user_controller import user_router
from config import Config
from dao import AsyncRedis
from service import AlgoliaService, HTTPService, RoleRequired

router = APIRouter()
router.include_router(auth_router)
router.include_router(category_router)
router.include_router(content_router)
router.include_router(file_router)
router.include_router(folder_router)
router.include_router(tag_router)
router.include_router(user_router)

__all__ = ['router']


@router.get('/bing', response_model=str)
async def get_bing_image(redis: Redis = Depends(AsyncRedis.get_connection)):
    url: bytes = await redis.get('bing_image_url')
    if url is None:
        return await HTTPService.parse_bing_image_url()
    return url.decode()


@router.get(
    '/refresh_algolia',
    response_model=int,
    dependencies=[Depends(RoleRequired('admin'))]
)
async def refresh_algolia_index(passcode: str):
    if passcode != Config.admin.password:
        return 0
    return await AlgoliaService.refresh_all_contents()
