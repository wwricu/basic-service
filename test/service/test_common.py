import asyncio

import pytest
from loguru import logger as log
from sqlalchemy import func, select

from wwricu.service.common import reset_sys_config
from wwricu.component.cache import sys_cache
from wwricu.component.database import get_session
from wwricu.domain.enum import CacheKeyEnum, PostStatusEnum, TagTypeEnum
from wwricu.domain.entity import BlogPost, PostTag


@pytest.mark.asyncio
async def test_system_count():
    await reset_sys_config()
    post_count, category_count, tag_count = await asyncio.gather(
        sys_cache.get(CacheKeyEnum.POST_COUNT),
        sys_cache.get(CacheKeyEnum.CATEGORY_COUNT),
        sys_cache.get(CacheKeyEnum.TAG_COUNT)
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
    async with get_session() as s:
        assert post_count == await s.scalar(post_stmt)
        assert tag_count == await s.scalar(tag_stmt)
        assert category_count == await s.scalar(category_stmt)
