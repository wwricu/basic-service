from collections import defaultdict

from sqlalchemy import select, update, func, delete, desc, Select

from wwricu.component.database import get_session
from wwricu.domain.entity import BlogPost, EntityRelation, PostTag
from wwricu.domain.enum import PostStatusEnum, RelationTypeEnum, TagTypeEnum
from wwricu.domain.tag import TagQueryDTO


async def build_criteria(query: TagQueryDTO) -> Select:
    stmt = select(PostTag)
    if query.type is not None:
        stmt = stmt.where(PostTag.type == query.type)
    if query.deleted is not None:
        stmt = stmt.where(PostTag.deleted == query.deleted)
    if query.tag_ids is not None:
        stmt = stmt.where(PostTag.id.in_(query.tag_ids))
    if query.name is not None:
        stmt = stmt.where(PostTag.name == query.name)
    return stmt


async def find_by_criteria(query: TagQueryDTO) -> list[PostTag]:
    stmt = await build_criteria(query)
    stmt = stmt.order_by(desc(PostTag.create_time))
    if query.page_size and query.page_size > 0 and query.page_index and query.page_index > 0:
        query.page_size = min(query.page_size, 100)
        stmt = stmt.limit(query.page_size).offset((query.page_index - 1) * query.page_size)
    async with get_session() as s:
        return list((await s.scalars(stmt)).all())


async def count(query: TagQueryDTO) -> int:
    stmt = await build_criteria(query)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    async with get_session() as s:
        return await s.scalar(count_stmt) or 0


async def refresh_tag_counts():
    published = select(func.count()).select_from(BlogPost).where(BlogPost.deleted == False,
                                                                 BlogPost.status == PostStatusEnum.PUBLISHED)
    tag_count = published.join(EntityRelation, EntityRelation.src_id == BlogPost.id).where(
        EntityRelation.dst_id == PostTag.id,
        EntityRelation.type == RelationTypeEnum.POST_TAG,
        EntityRelation.deleted == False).correlate(PostTag).scalar_subquery()
    category_count = published.where(BlogPost.category_id == PostTag.id).correlate(PostTag).scalar_subquery()
    async with get_session() as s:
        await s.execute(update(PostTag).where(PostTag.type == TagTypeEnum.POST_TAG).values(count=tag_count))
        await s.execute(update(PostTag).where(PostTag.type == TagTypeEnum.POST_CAT).values(count=category_count))


async def find_tags_by_posts(post_list: list[BlogPost]) -> dict[int, list[PostTag]]:
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
    result = defaultdict(list)
    for post_tag, post_id in query_result:
        result[post_id].append(post_tag)
    return result


async def update_selective(tag_id: int, **kwargs):
    stmt = update(PostTag).where(PostTag.id == tag_id).where(PostTag.deleted == False).values(**kwargs)
    async with get_session() as s:
        await s.execute(stmt)


async def find_ids_by_post_id(post_id: int) -> list[int]:
    stmt = select(EntityRelation.dst_id).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.deleted == False).where(
        EntityRelation.src_id == post_id
    )
    async with get_session() as s:
        return list((await s.scalars(stmt)).all())


async def delete_unlink_relation():
    post_query = ~select(BlogPost.id).where(BlogPost.id == EntityRelation.src_id).exists()
    tag_query = ~select(PostTag.id).where(PostTag.id == EntityRelation.dst_id).exists()
    stmt = delete(EntityRelation).where(post_query | tag_query)
    async with get_session() as s:
        await s.execute(stmt)


async def find_category(category_id: int | None = None, name: str | None = None) -> PostTag | None:
    if category_id is None and name is None:
        return None
    query = TagQueryDTO(type=TagTypeEnum.POST_CAT)
    if category_id is not None:
        query.tag_ids = [category_id]
    if name is not None:
        query.name = name
    if len(tags := await find_by_criteria(query)) > 1:
        raise ValueError
    return tags[0] if tags else None
