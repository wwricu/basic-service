import asyncio

import pytest
from loguru import logger as log
from sqlalchemy import func, select

from wwricu.service.common import reset_system_count
from wwricu.service.cache import cache
from wwricu.service.database import new_session
from wwricu.domain.enum import CacheKeyEnum, PostStatusEnum, TagTypeEnum
from wwricu.domain.entity import BlogPost, PostTag


@pytest.mark.asyncio
async def test_system_count():
    await reset_system_count()
    post_count, category_count, tag_count = await asyncio.gather(
        cache.get(CacheKeyEnum.POST_COUNT),
        cache.get(CacheKeyEnum.CATEGORY_COUNT),
        cache.get(CacheKeyEnum.TAG_COUNT)
    )
    post_stmt = select(func.count(BlogPost.id)).where(
        BlogPost.deleted == False).where(
        BlogPost.status == PostStatusEnum.PUBLISHED
    )
    category_stmt = select(func.count(PostTag.id)).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_CAT
    )
    tag_stmt = select(func.count(PostTag.id)).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_TAG
    )
    log.info(f'{post_count=} {category_count=} {tag_count=}')
    async with new_session() as session:
        assert post_count == await session.scalar(post_stmt)
        assert tag_count == await session.scalar(tag_stmt)
        assert category_count == await session.scalar(category_stmt)
