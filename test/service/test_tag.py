import pytest

from loguru import logger as log
from sqlalchemy import select

from wwricu.domain.entity import BlogPost, EntityRelation, PostTag
from wwricu.domain.enum import RelationTypeEnum, TagTypeEnum
from wwricu.service.database import get_session
from wwricu.service.tag import get_posts_tag_lists


@pytest.mark.asyncio
async def test_get_posts_tag_lists():
    post_list = [BlogPost(id=25)]
    result = await get_posts_tag_lists(post_list)
    log.info(result)


@pytest.mark.asyncio
async def test_get_posts_tags_sql():
    post_list = [BlogPost(id=25)]
    stmt = select(PostTag, EntityRelation.src_id).join(
        EntityRelation, PostTag.id == EntityRelation.dst_id).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_TAG).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.deleted == False).where(
        EntityRelation.src_id.in_(post.id for post in post_list)
    )
    async with get_session() as session:
        query_result = (await session.execute(stmt)).all()
        log.info(query_result)

        result = {post.id: [] for post in post_list}
        for post_tag, post_id in query_result:
            log.info(post_tag.name, post_id)
            if (post_tag_list := result.get(post_id)) is not None:
                post_tag_list.append(post_tag)
                log.info(result.get(25))
                log.info(post_tag_list)
        log.info(result)
