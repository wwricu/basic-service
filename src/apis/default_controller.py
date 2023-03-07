from fastapi import APIRouter, Depends
from redis import Redis

from config import Config
from dao import AsyncRedis
from service import AlgoliaService, APIThrottle, HTTPService


default_router = APIRouter(prefix='/default', tags=['default'])


@default_router.get(
    '/bing', response_model=str,
    dependencies=[Depends(APIThrottle(60))]
)
async def get_bing_image(redis: Redis = Depends(AsyncRedis.get_connection)):
    url: bytes = await redis.get('bing_image_url')
    if url is None:
        return await HTTPService.parse_bing_image_url()
    return url.decode()


@default_router.get(
    '/refresh_algolia',
    response_model=int,
    dependencies=[Depends(APIThrottle(60))]
)
async def refresh_algolia_index(passcode: str):
    if passcode != Config.admin.password:
        return 0
    return await AlgoliaService.refresh_all_contents()
