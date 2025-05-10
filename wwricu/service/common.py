import asyncio
import datetime
import time
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from loguru import logger as log
from sqlalchemy import select, func, delete

from wwricu.config import Config
from wwricu.domain.entity import BlogPost, EntityRelation, PostTag, PostResource
from wwricu.domain.enum import CacheKeyEnum, PostStatusEnum, TagTypeEnum, RelationTypeEnum
from wwricu.service.cache import cache
from wwricu.service.category import reset_category_count
from wwricu.service.database import database_backup, engine, get_session, new_session
from wwricu.service.storage import oss_public
from wwricu.service.tag import reset_tag_count


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = AsyncIOScheduler()
    try:
        scheduler.add_job(hard_delete_expiration, trigger=CronTrigger(hour=5))
        scheduler.add_job(clean_post_resource, trigger=CronTrigger(day_of_week=0, hour=4))
        scheduler.add_job(database_backup, trigger=CronTrigger(day_of_week=0, hour=3))
        scheduler.start()
        await reset_tag_count()
        await reset_category_count()
        await reset_system_count()
        await cache.set(CacheKeyEnum.STARTUP_TIMESTAMP, int(time.time()), 0)
        log.info('App startup')
        yield
    finally:
        scheduler.shutdown()
        await cache.close()
        await engine.dispose()
        database_backup()
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
    deadline = datetime.datetime.now() - datetime.timedelta(days=Config.trash_expire_day)

    deleted_posts = select(BlogPost.id).where(
        BlogPost.deleted == True).where(
        BlogPost.update_time < deadline
    ).subquery()
    deleted_tags = select(PostTag.id).where(
        PostTag.deleted == True).where(
        PostTag.type == TagTypeEnum.POST_TAG).where(
        PostTag.update_time < deadline
    ).subquery()

    async with new_session() as s:
        # delete posts
        stmt = delete(BlogPost).where(BlogPost.id.in_(deleted_posts.c.id))
        result = await s.execute(stmt)
        log.info(f'{result.rowcount} post deleted')

        # delete post relations
        stmt = delete(EntityRelation).where(
            EntityRelation.type.in_((RelationTypeEnum.POST_TAG, RelationTypeEnum.POST_RES))).where(
            EntityRelation.src_id.in_(deleted_posts.c.id)
        )
        await s.execute(stmt)

        # delete tag relations
        stmt = delete(EntityRelation).where(
            EntityRelation.type == RelationTypeEnum.POST_TAG).where(
            EntityRelation.dst_id.in_(deleted_tags.c.id)
        )
        await s.execute(stmt)

        # delete categories
        stmt = delete(PostTag).where(
            PostTag.deleted == True).where(
            PostTag.type.in_((TagTypeEnum.POST_CAT, TagTypeEnum.POST_TAG))).where(
            PostTag.update_time < deadline
        )
        result = await s.execute(stmt)
        log.info(f'{result.rowcount} tags and categories deleted')


async def clean_post_resource():
    """
    Mark post resources deleted when all related posts are hard deleted.
    Post soft deleted ->
    Post expired, post hard deleted, relation hard deleted ->
    All relations hard deleted, resource hard deleted, oss file deleted;
    """
    log.info('start cleaning post resources')
    query = select(PostResource.id).join(
        EntityRelation, PostResource.id == EntityRelation.dst_id).where(
        PostResource.deleted == False).where(
        EntityRelation.deleted == False).where(
        EntityRelation.type == RelationTypeEnum.POST_RES).having(
        func.count(EntityRelation.id) <= 0
    ).subquery()

    async with new_session() as s:
        stmt = select(PostResource).where(PostResource.id.in_(query.c.id))
        deleted_resources = await s.scalars(stmt)
        oss_public.batch_delete([resource.key for resource in deleted_resources.all()])

        stmt = delete(PostResource).where(PostResource.id.in_(query.c.id))
        result = await s.execute(stmt)
        log.info(f'Delete {result.rowcount} unreferenced resources')
