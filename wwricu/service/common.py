import asyncio
import functools
import sys
import time
import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path

from anyio import open_file
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from loguru import logger as log

from wwricu.component import database as database_manager
from wwricu.component.cache import LocalCache, image_cache, sys_cache
from wwricu.component.storage import storage
from wwricu.config import app_config, env
from wwricu.database import post_db, tag_db
from wwricu.domain.constant import CommonConst, TimeConst
from wwricu.domain.enum import CacheKeyEnum, PostStatusEnum, TagTypeEnum
from wwricu.domain.post import PostQueryDTO
from wwricu.domain.tag import TagQueryDTO


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    try:

        await download_database()
        await database_manager.init()
        LocalCache.init()

        scheduler.add_job(backup_database, trigger=CronTrigger(day_of_week=0, hour=3))
        scheduler.add_job(tag_db.delete_unlink_relation, trigger=CronTrigger(day_of_week=0, hour=4))
        scheduler.start()

        await sys_cache.set(CacheKeyEnum.STARTUP_TIMESTAMP, int(time.time()), 0)

        log.info(f'{app.title} startup')
        yield
    finally:
        scheduler.shutdown()
        await LocalCache.shutdown()
        await upload_database()
        await database_manager.close()
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
    url = storage.generate_presigned_url(key, expires=2 * TimeConst.ONE_HOUR_SECONDS)
    await image_cache.set(key, url, second=TimeConst.ONE_HOUR_SECONDS)
    return url


async def download_database(path: str = app_config.database.name):
    if Path(path).exists():
        return
    if not (data := await storage.get(app_config.database.name)):
        raise FileNotFoundError(f'Cloud database {app_config.database.name} not found')
    log.info(f'Download database as {path}')
    async with await open_file(path, mode='wb+') as f:
        await f.write(data)


def lock_database(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async with database_lock:
            return await func(*args, **kwargs)
    return wrapper


async def backup_database():
    await upload_database(CommonConst.DATABASE_BACKUP_KEY)


@lock_database
async def upload_database(key: str = app_config.database.name):
    if env.is_dev:
        return
    await database_manager.backup(backup_path := uuid.uuid4().hex)
    try:
        async with await open_file(backup_path, mode='rb') as f:
            await storage.put(key, await f.read())
            log.info(f'Upload database to {key} success')
    finally:
        Path(backup_path).unlink(missing_ok=True)


@lock_database
async def restore_database():
    if env.is_dev:
        return
    file = Path(backup_path := uuid.uuid4().hex)
    await download_database(backup_path)
    try:
        await database_manager.close()
        file.replace(app_config.database.name)
        await database_manager.init()
    except Exception as e:
        log.error(e)
        file.unlink(missing_ok=True)
        sys.exit(1)


database_lock = asyncio.Lock()
