from datetime import datetime

from sqlalchemy import select, update, func, case, delete, desc

from wwricu.component.database import get_session
from wwricu.domain.entity import BlogPost, EntityRelation, PostTag
from wwricu.domain.enum import PostStatusEnum, RelationTypeEnum, TagTypeEnum
from wwricu.domain.tag import TagRequestRO


async def get_tags_by_ids(tag_ids: list[int]) -> list[PostTag]:
    if not tag_ids:
        return []
    stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_TAG).where(
        PostTag.deleted == False).where(
        PostTag.id.in_(tag_ids)
    )
    async with get_session() as s:
        return list((await s.scalars(stmt)).all())


async def reset_tag_count():
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


async def is_tag_exists(tag_name: str, tag_type: TagTypeEnum) -> bool:
    stmt = select(func.count(PostTag.id)).where(
        PostTag.deleted == False).where(
        PostTag.type == tag_type).where(
        PostTag.name == tag_name
    )
    async with get_session() as s:
        return await s.scalar(stmt) > 0


async def get_tag_count() -> int:
    stmt = select(func.count(PostTag.id)).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_TAG
    )
    async with get_session() as s:
        return await s.scalar(stmt)


async def update_tag_post_count(prev_tag_ids: set[int], post_tag_ids: set[int]) -> None:
    stmt = update(PostTag).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_TAG).where(
        PostTag.id.in_(prev_tag_ids | post_tag_ids)).values(
        count=case(
            (PostTag.id.in_(prev_tag_ids - post_tag_ids), PostTag.count - 1),
            (PostTag.id.in_(post_tag_ids - prev_tag_ids), PostTag.count + 1),
            else_=PostTag.count
        )
    )
    async with get_session() as s:
        await s.execute(stmt)


async def increase_post_tag_count(post_tag_ids: list[int], increment: int):
    stmt = update(PostTag).where(PostTag.id.in_(post_tag_ids)).values(count=PostTag.count + increment)
    async with get_session() as s:
        await s.execute(stmt)


async def get_tags_by_posts(post_list: list[BlogPost]) -> dict[int, list[PostTag]]:
    if not post_list:
        return {}
    stmt = select(PostTag, EntityRelation.src_id).join(
        EntityRelation, PostTag.id == EntityRelation.dst_id).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_TAG).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.deleted == False).where(
        EntityRelation.src_id.in_(post.id for post in post_list)
    )
    async with get_session() as s:
        query_result = (await s.execute(stmt)).all()
        result = {post.id: [] for post in post_list}
        for post_tag, post_id in query_result:
            if post_tag_list := result.get(post_id):
                post_tag_list.append(post_tag)
        return result


async def delete_tag_before(deadline: datetime):
    deleted_tags = select(PostTag.id).where(
        PostTag.deleted == True).where(
        PostTag.type == TagTypeEnum.POST_TAG).where(
        PostTag.update_time < deadline
    )
    tag_stmt = delete(EntityRelation).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.dst_id.in_(deleted_tags)
    )
    stmt = delete(PostTag).where(
        PostTag.deleted == True).where(
        PostTag.type.in_((TagTypeEnum.POST_CAT, TagTypeEnum.POST_TAG))).where(
        PostTag.update_time < deadline
    )
    async with get_session() as s:
        await s.execute(tag_stmt)
        await s.execute(stmt)


async def update_tag_selective(tag_id: int, **kwargs):
    stmt = update(PostTag).where(PostTag.id == tag_id).where(PostTag.deleted == False).values(**kwargs)
    async with get_session() as s:
        await s.execute(stmt)


async def get_tag_by_type(get_tag: TagRequestRO) -> list[PostTag]:
    stmt = select(PostTag).where(
        PostTag.deleted == False).where(
        PostTag.type == get_tag.type).order_by(
        desc(PostTag.create_time)
    )
    if get_tag.page_index > 0 and get_tag.page_size > 0:
        stmt = stmt.limit(get_tag.page_size).offset((get_tag.page_index - 1) * get_tag.page_size)
    async with get_session() as s:
        return list((await s.scalars(stmt)).all())


async def get_tag_by_id(tag_id: int) -> PostTag:
    stmt = select(PostTag).where(PostTag.id == tag_id).where(PostTag.deleted == False)
    async with get_session() as s:
        return await s.scalar(stmt)


async def get_all_deleted_tags(deadline: datetime) -> list[PostTag]:
    stmt = select(PostTag).where(PostTag.deleted == True).where(PostTag.update_time > deadline)
    async with get_session() as s:
        return list((await s.scalars(stmt)).all())
