from datetime import datetime

from sqlalchemy import select, update, func, delete, desc, Select
from sqlalchemy.orm import defer

from wwricu.component.database import get_session
from wwricu.domain.entity import BlogPost, EntityRelation, PostTag
from wwricu.domain.enum import PostStatusEnum, RelationTypeEnum, TagTypeEnum
from wwricu.domain.post import PostQueryDTO


async def find_by_id(post_id: int) -> BlogPost | None:
    stmt = select(BlogPost).where(BlogPost.id == post_id).where(BlogPost.deleted == False)
    async with get_session() as s:
        return await s.scalar(stmt)


async def find_by_ids_by_tags(tag_names: list[str]) -> list[int]:
    if not tag_names:
        return []
    stmt = select(BlogPost.id).join(
        PostTag, BlogPost.id == EntityRelation.src_id).join(
        EntityRelation, PostTag.id == EntityRelation.dst_id).where(
        PostTag.deleted == False).where(
        EntityRelation.deleted == False).where(
        BlogPost.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_TAG).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        PostTag.name.in_(tag_names)
    )
    async with get_session() as s:
        return list((await s.scalars(stmt)).all())


async def delete_before(deadline: datetime):
    deleted_posts = select(BlogPost.id).where(
        BlogPost.deleted == True).where(
        BlogPost.update_time < deadline
    )
    post_stmt = delete(BlogPost).where(BlogPost.id.in_(deleted_posts))
    stmt = delete(EntityRelation).where(
        EntityRelation.type.in_((RelationTypeEnum.POST_TAG, RelationTypeEnum.POST_RES))).where(
        EntityRelation.src_id.in_(deleted_posts)
    )
    async with get_session() as s:
        await s.execute(post_stmt)
        await s.execute(stmt)


async def update_selective(post_id: int, **kwargs):
    stmt = update(BlogPost).where(BlogPost.id == post_id).where(BlogPost.deleted == False).values(**kwargs)
    async with get_session() as s:
        await s.execute(stmt)


async def find_published(post_id: int) -> BlogPost | None:
    stmt = select(BlogPost).where(
        BlogPost.id == post_id).where(
        BlogPost.deleted == False).where(
        BlogPost.status == PostStatusEnum.PUBLISHED
    )
    async with get_session() as s:
        return await s.scalar(stmt)


async def find_by_criteria(query: PostQueryDTO) -> list[BlogPost]:
    stmt = await build_criteria(query)
    if query.page_size is not None and query.page_index is not None:
        stmt = stmt.order_by(
            desc(BlogPost.create_time)).limit(
            query.page_size).offset(
            (query.page_index - 1) * query.page_size
        )
    async with get_session() as s:
        posts_result = await s.scalars(stmt)
        return list(posts_result.all())


async def count(query: PostQueryDTO) -> int:
    stmt = await build_criteria(query)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    async with get_session() as s:
        return await s.scalar(count_stmt) or 0


async def build_criteria(query: PostQueryDTO) -> Select:
    stmt = select(BlogPost).options(defer(BlogPost.content, raiseload=True))
    if query.status is not None:
        stmt = stmt.where(BlogPost.status == query.status.value)
    if query.deleted is not None:
        stmt = stmt.where(BlogPost.deleted == query.deleted)
    if query.category_id is not None:
        stmt = stmt.where(BlogPost.category_id == query.category_id)
    if query.post_ids is not None:
        stmt = stmt.where(BlogPost.id.in_(query.post_ids))
    if query.deadline is not None:
        stmt = stmt.where(BlogPost.update_time > query.deadline)
    return stmt
