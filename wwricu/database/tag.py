from collections import defaultdict
from datetime import datetime

from sqlalchemy import select, update, func, case, delete, desc, Select

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
    if query.deadline is not None:
        stmt = stmt.where(PostTag.update_time > query.deadline)
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


async def update_tag_post_count(prev_tag_ids: set[int], post_tag_ids: set[int]):
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
    stmt = delete(PostTag).where(PostTag.deleted == True).where(PostTag.update_time < deadline)
    async with get_session() as s:
        await s.execute(tag_stmt)
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


async def update_category_count(post: BlogPost, increment: int = 1):
    stmt = update(PostTag).where(
        PostTag.id == post.category_id).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_CAT).values(
        count=PostTag.count + increment
    )
    async with get_session() as s:
        await s.execute(stmt)


async def reset_category_count():
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


async def update_category_post_count(prev_category_id: int | None, post_category_id: int | None):
    if prev_category_id == post_category_id:
        return
    stmt = update(PostTag).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_CAT).where(
        PostTag.id.in_((prev_category_id, post_category_id))).values(
        count=case(
            (PostTag.id == prev_category_id, PostTag.count - 1),
            (PostTag.id == post_category_id, PostTag.count + 1),
            else_=PostTag.count
        )
    )
    async with get_session() as s:
        await s.execute(stmt)


async def update_selective(tag_id: int, **kwargs):
    stmt = update(PostTag).where(PostTag.id == tag_id).where(PostTag.deleted == False).values(**kwargs)
    async with get_session() as s:
        await s.execute(stmt)


async def delete_post_tags(post_id: int):
    stmt = update(EntityRelation).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.deleted == False).where(
        EntityRelation.src_id == post_id).values(
        deleted=True
    )
    async with get_session() as s:
        await s.execute(stmt)


async def find_tag_ids_by_post_id(post_id: int) -> list[int]:
    stmt = select(EntityRelation.dst_id).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.deleted == False).where(
        EntityRelation.src_id == post_id
    )
    async with get_session() as s:
        return list((await s.scalars(stmt)).all())
