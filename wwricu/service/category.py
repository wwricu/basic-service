from sqlalchemy import select, update, func

from wwricu.domain.entity import BlogPost, PostTag
from wwricu.domain.enum import TagTypeEnum, PostStatusEnum
from wwricu.service.database import session, new_session


async def get_category_by_id(category_id: int) -> PostTag:
    stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_CAT).where(
        PostTag.deleted == False).where(
        PostTag.id == category_id
    )
    return await session.scalar(stmt)


async def get_category_by_name(category_name: str) -> PostTag | None:
    if category_name is None:
        return None
    stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_CAT).where(
        PostTag.deleted == False).where(
        PostTag.name == category_name
    )
    return await session.scalar(stmt)


async def update_category_count(post: BlogPost, increment: int = 1) -> int:
    stmt = update(PostTag).where(
        PostTag.id == post.category_id).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_CAT).values(
        count=PostTag.count + increment
    )
    result = await session.execute(stmt)
    return result.rowcount


async def update_category(post: BlogPost, category_id: int | None = None) -> PostTag | None:
    if category_id is None:
        return None
    category = await get_category_by_id(category_id)
    if category is None:
        return None
    stmt = update(BlogPost).where(
        BlogPost.id == post.id).where(
        BlogPost.deleted == False
    ).values(category_id=category.id)
    await session.execute(stmt)
    return category


async def get_post_category(post: BlogPost) -> PostTag:
    stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_CAT).where(
        PostTag.deleted == False).where(
        PostTag.id == post.category_id
    )
    return await session.scalar(stmt)


async def get_posts_category(post_list: list[BlogPost]) -> dict[int, PostTag]:
    if not post_list:
        return dict()
    cat_stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_CAT).where(
        PostTag.deleted == False).where(
        PostTag.id.in_([post.category_id for post in post_list])
    )
    category_dict = {cat.id: cat for cat in (await session.scalars(cat_stmt)).all()}
    return {post.id: category_dict.get(post.category_id) for post in post_list}


async def reset_category_count():
    async with new_session() as s:
        subquery = select(PostTag.id, func.count(BlogPost.id).label('post_count')).join(
            BlogPost, PostTag.id == BlogPost.category_id).where(
            PostTag.deleted == False).where(
            BlogPost.deleted == False).where(
            PostTag.type == TagTypeEnum.POST_CAT).where(
            BlogPost.status == PostStatusEnum.PUBLISHED
        ).group_by(PostTag.id).subquery()
        stmt = update(PostTag).where(PostTag.id == subquery.c.id).values(count=subquery.c.post_count)
        await s.execute(stmt)
