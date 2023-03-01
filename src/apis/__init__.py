from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from apis.auth_controller import auth_router
from apis.category_controller import category_router
from apis.content_controller import content_router
from apis.file_controller import file_router
from apis.folder_controller import folder_router
from apis.tag_controller import tag_router
from apis.user_controller import user_router
from dao import AsyncRedis
from service import HTTPService

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
