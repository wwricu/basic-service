import time
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from loguru import logger as log

from wwricu.component.cache import sys_cache, LocalCache, image_cache
from wwricu.component.database import database_manager
from wwricu.component.storage import storage
from wwricu.config import app_config
from wwricu.database import post_db, tag_db
from wwricu.domain.constant import TimeConst
from wwricu.domain.enum import CacheKeyEnum, PostStatusEnum, TagTypeEnum
from wwricu.domain.post import PostQueryDTO
from wwricu.domain.tag import TagQueryDTO


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    try:
        LocalCache.init()
        scheduler.add_job(database_manager.backup, trigger=CronTrigger(day_of_week=0, hour=3))
        scheduler.add_job(tag_db.delete_unlink_relation, trigger=CronTrigger(day_of_week=0, hour=4))
        scheduler.start()

        await sys_cache.set(CacheKeyEnum.STARTUP_TIMESTAMP, int(time.time()), 0)

        log.info(f'image qps={app_config.security.image_ip_qps} open api qps={app_config.security.open_ip_qps}')
        log.info(f'allow {app_config.security.login_ip_times} logins in {app_config.security.login_ip_span} seconds')
        log.info(f'{app.title} startup')
        yield
    finally:
        scheduler.shutdown()
        await database_manager.close()
        await LocalCache.shutdown()
        log.info(f'{app.title} Exit')
        await log.complete()


async def reset_sys_config():
    yield
    post_count = await post_db.count(PostQueryDTO(status=PostStatusEnum.PUBLISHED))
    category_count = await tag_db.count(TagQueryDTO(type=TagTypeEnum.POST_CAT))
    tag_count = await tag_db.count(TagQueryDTO(type=TagTypeEnum.POST_TAG))
    log.info(f'{post_count=} {category_count=} {tag_count=}')
    await sys_cache.set(CacheKeyEnum.POST_COUNT, post_count, 0)
    await sys_cache.set(CacheKeyEnum.CATEGORY_COUNT, category_count, 0)
    await sys_cache.set(CacheKeyEnum.TAG_COUNT, tag_count, 0)


async def get_image_url(key: str) -> str:
    if url := await image_cache.get(key):
        return url
    url = storage.generate_presigned_url(key, expires=2 * TimeConst.ONE_DAY_SECONDS)
    await image_cache.set(key, url, second=TimeConst.ONE_DAY_SECONDS)
    return url
