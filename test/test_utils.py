import secrets
from random import Random

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, update, func

from wwricu.component.database import get_session
from wwricu.domain.entity import Base, BlogPost, EntityRelation, PostResource, PostTag
from wwricu.domain.enum import TagTypeEnum, RelationTypeEnum, PostStatusEnum
from wwricu.main import app


@pytest.mark.skip
def test_show_ddl():
    sync_engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(sync_engine)


@pytest.mark.skip
@pytest.mark.asyncio
async def test_refresh_post_id():
    stmt = select(BlogPost)
    async with get_session() as s:
        posts = await s.scalars(stmt)

    async with get_session() as s:
        for post in posts:
            new_id = 1_000_000_000 + secrets.randbelow(9_000_000_000)
            await s.execute(update(BlogPost).where(BlogPost.id == post.id).values(id = new_id))
            await s.execute(update(EntityRelation).where(EntityRelation.src_id == post.id).values(src_id = new_id))
            await s.execute(update(PostResource).where(PostResource.post_id == post.id).values(post_id = new_id))


@pytest.mark.skip
@pytest.mark.asyncio
async def test_reset_count():
    subquery = select(PostTag.id, func.count(BlogPost.id).label('tag_count')).join(
        EntityRelation, PostTag.id == EntityRelation.dst_id).join(
        BlogPost, EntityRelation.src_id == BlogPost.id).where(
        PostTag.deleted == False).where(
        EntityRelation.deleted == False).where(
        BlogPost.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_TAG).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        BlogPost.status == PostStatusEnum.PUBLISHED).group_by(
        PostTag.id
    ).subquery()
    stmt = update(PostTag).where(PostTag.id == subquery.c.id).values(count=subquery.c.tag_count)
    async with get_session() as s:
        await s.execute(stmt)

    subquery = select(PostTag.id, func.count(BlogPost.id).label('category_count')).join(
        BlogPost, PostTag.id == BlogPost.category_id).where(
        PostTag.deleted == False).where(
        BlogPost.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_CAT).where(
        BlogPost.status == PostStatusEnum.PUBLISHED
    ).group_by(PostTag.id).subquery()
    stmt = update(PostTag).where(PostTag.id == subquery.c.id).values(count=subquery.c.category_count)
    async with get_session() as s:
        await s.execute(stmt)


client = TestClient(app)
random = Random()
