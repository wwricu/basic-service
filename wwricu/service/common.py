import asyncio
import datetime
import time
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from loguru import logger as log

from wwricu.component.cache import cache
from wwricu.component.database import database_backup, engine
from wwricu.component.storage import oss_public
from wwricu.config import Config
from wwricu.database import post_db, res_db, tag_db
from wwricu.domain.enum import CacheKeyEnum, PostStatusEnum, TagTypeEnum
from wwricu.domain.post import PostQueryDTO
from wwricu.domain.tag import TagQueryDTO


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = AsyncIOScheduler()
    try:
        scheduler.add_job(purge_expired_entities, trigger=CronTrigger(hour=5))
        scheduler.add_job(cleanup_orphan_resources, trigger=CronTrigger(day_of_week=0, hour=4))
        scheduler.add_job(database_backup, trigger=CronTrigger(day_of_week=0, hour=3))
        scheduler.start()

        await tag_db.reset_tag_count()
        await tag_db.reset_category_count()
        await init_public_counts()

        await cache.set(CacheKeyEnum.STARTUP_TIMESTAMP, int(time.time()), 0)
        log.info('App startup')
        yield
    finally:
        scheduler.shutdown()
        await cache.close()
        await engine.dispose()
        if not __debug__:
            await database_backup()
        log.info('Exit')
        await log.complete()


async def init_public_counts():
    post_count = await post_db.get_posts_count(PostQueryDTO(status=PostStatusEnum.PUBLISHED))
    category_count = await tag_db.get_tags_count(TagQueryDTO(type=TagTypeEnum.POST_CAT))
    tag_count = await tag_db.get_tags_count(TagQueryDTO(type=TagTypeEnum.POST_TAG))
    log.info(f'{post_count=} {category_count=} {tag_count=}')
    await asyncio.gather(
        cache.set(CacheKeyEnum.POST_COUNT, post_count, 0),
        cache.set(CacheKeyEnum.CATEGORY_COUNT, category_count, 0),
        cache.set(CacheKeyEnum.TAG_COUNT, tag_count, 0)
    )


async def purge_expired_entities():
    log.info('hard deleting expired entities')
    deadline = datetime.datetime.now() - datetime.timedelta(days=Config.trash_expire_day)
    await post_db.delete_post_before(deadline)
    await tag_db.delete_tag_before(deadline)


async def cleanup_orphan_resources():
    """
    Mark post resources deleted when all related posts are hard deleted.
    Post soft deleted ->
    Post expired, post hard deleted, relation hard deleted ->
    All relations hard deleted, resource hard deleted, oss file deleted;
    """
    log.info('start cleaning post resources')
    deleted_resources = await res_db.cleanup_unlinked_resources()
    await oss_public.batch_delete([resource.key for resource in deleted_resources])
