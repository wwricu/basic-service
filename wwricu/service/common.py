import asyncio
import datetime
import time
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from loguru import logger as log
from sqlalchemy import select, func, delete

from wwricu.domain.entity import BlogPost, EntityRelation, PostTag, PostResource
from wwricu.domain.enum import CacheKeyEnum, PostStatusEnum, TagTypeEnum, RelationTypeEnum
from wwricu.config import Config
from wwricu.service.cache import cache
from wwricu.service.category import reset_category_count
from wwricu.service.database import engine, get_session, new_session
from wwricu.service.storage import oss
from wwricu.service.tag import reset_tag_count


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = AsyncIOScheduler()
    try:
        scheduler.add_job(hard_delete_expiration, trigger=CronTrigger(hour=3, minute=0, second=0))
        scheduler.add_job(clean_post_resource, trigger=CronTrigger(day=1, hour=3, minute=0, second=0))
        scheduler.start()
        await reset_tag_count()
        await reset_category_count()
        await reset_system_count()
        await cache.set(CacheKeyEnum.STARTUP_TIMESTAMP, int(time.time()), 0)
        log.info(f'listening on {Config.host}:{Config.port}')
        yield
    finally:
        scheduler.shutdown()
        await cache.close()
        await engine.dispose()
        log.info('Exit')
        await log.complete()


async def reset_system_count():
    post_stmt = select(
        func.count(BlogPost.id)).where(
        BlogPost.deleted == False).where(
        BlogPost.status == PostStatusEnum.PUBLISHED
    )
    category_stmt = select(
        func.count(PostTag.id)).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_CAT
    )
    tag_stmt = select(
        func.count(PostTag.id)).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_TAG
    )
    async with new_session() as s:
        # single session with transaction cannot be used by gather
        post_count = await s.scalar(post_stmt)
        category_count = await s.scalar(category_stmt)
        tag_count = await s.scalar(tag_stmt)
        log.info(f'{post_count=} {category_count=} {tag_count=}')
        await asyncio.gather(
            cache.set(CacheKeyEnum.POST_COUNT, post_count, 0),
            cache.set(CacheKeyEnum.CATEGORY_COUNT, category_count, 0),
            cache.set(CacheKeyEnum.TAG_COUNT, tag_count, 0)
        )


async def update_system_count():
    async with get_session() as s:
        yield
        await s.flush()
        await reset_system_count()


async def hard_delete_expiration():
    log.info('hard deleting expired entities')
    async with new_session() as s:
        deadline = datetime.datetime.now() - datetime.timedelta(days=Config.trash_expire_day)
        stmt = select(BlogPost).where(BlogPost.deleted == True).where(BlogPost.update_time < deadline)
        deleted_posts = await s.scalar(stmt)
        stmt = delete(BlogPost).where(BlogPost.id.in_(post.id for post in deleted_posts))
        # delete posts
        result = await s.scalar(stmt)
        log.info(f'{result.rowcount} post deleted')

        stmt = delete(EntityRelation).where(
            EntityRelation.type.in_((RelationTypeEnum.POST_TAG, RelationTypeEnum.POST_RES))).where(
            EntityRelation.src_id.in_(post.id for post in deleted_posts)
        )
        # delete post relations
        await s.execute(stmt)

        stmt = select(PostTag).where(
            PostTag.deleted == True).where(
            PostTag.type == TagTypeEnum.POST_TAG).where(
            PostTag.update_time < deadline
        )
        deleted_tags = await s.scalar(stmt)
        # delete tags
        result = await s.execute(stmt)
        log.info(f'{result.rowcount} tags deleted')

        stmt = delete(EntityRelation).where(
            EntityRelation.type == RelationTypeEnum.POST_TAG).where(
            EntityRelation.dst_id.in_(tag.id for tag in deleted_tags)
        )
        # delete tag relations
        await s.execute(stmt)

        stmt = delete(PostTag).where(
            PostTag.deleted == True).where(
            PostTag.type == TagTypeEnum.POST_CAT).where(
            PostTag.update_time < deadline
        )
        # delete categories
        result = await s.execute(stmt)
        log.info(f'{result.rowcount} categories deleted')


async def clean_post_resource():
    """delete all unused files from oss"""
    # TODO: soft delete not resources not referenced by posts
    log.info('start cleaning post resources')
    async with new_session() as s:
        resource_keys = await s.scalars(select(PostResource.key))
        resource_keys = set(resource_keys.all())
        all_s3_objects = oss.list_all()
        keys_to_del = list(filter(lambda key: key not in resource_keys, map(lambda r: r.Key, all_s3_objects)))
        log.warning(f'{len(keys_to_del)} objects to be deleted')
        oss.batch_delete(keys_to_del)
