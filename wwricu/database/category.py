from sqlalchemy import func, select, update, case

from wwricu.component.database import get_session
from wwricu.domain.entity import BlogPost, PostTag
from wwricu.domain.enum import PostStatusEnum, TagTypeEnum


async def get_category_by_name(category_name: str) -> PostTag | None:
    stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_CAT).where(
        PostTag.deleted == False).where(
        PostTag.name == category_name
    )
    async with get_session() as s:
        return await s.scalar(stmt)


async def update_category_count(post: BlogPost, increment: int = 1):
    stmt = update(PostTag).where(
        PostTag.id == post.category_id).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_CAT).values(
        count=PostTag.count + increment
    )
    async with get_session() as s:
        await s.execute(stmt)


async def get_category_by_id(category_id: int) -> PostTag:
    stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_CAT).where(
        PostTag.deleted == False).where(
        PostTag.id == category_id
    )
    async with get_session() as s:
        return await s.scalar(stmt)


async def get_categories_by_ids(category_ids: list[int]) -> list[PostTag]:
    if not category_ids:
        return []
    stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_CAT).where(
        PostTag.deleted == False).where(
        PostTag.id.in_(category_ids)
    )
    async with get_session() as s:
        return list((await s.scalars(stmt)).all())


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


async def get_category_count() -> int:
    stmt = select(func.count(PostTag.id)).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_CAT
    )
    async with get_session() as s:
        return await s.scalar(stmt)


async def update_category_post_count(prev_category_id: int, post_category_id: int):
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

