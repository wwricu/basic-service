from sqlalchemy import case, func, select, update

from wwricu.domain.entity import BlogPost, PostTag
from wwricu.domain.enum import PostStatusEnum, TagTypeEnum
from wwricu.domain.post import PostUpdateRO
from wwricu.service.database import new_session, session


async def get_category_by_name(category_name: str) -> PostTag | None:
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
    return (await session.execute(stmt)).rowcount


async def update_category(post: BlogPost, post_update: PostUpdateRO):
    stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_CAT).where(
        PostTag.deleted == False).where(
        PostTag.id == post_update.category_id
    )
    if (category := await session.scalar(stmt)) is None:
        return

    prev_category_id, post_category_id = None, None
    if post.status == PostStatusEnum.PUBLISHED:
        prev_category_id = post.category_id
    if post_update.status == PostStatusEnum.PUBLISHED:
        post_category_id = post.category_id

    if prev_category_id != post_category_id:
        stmt = update(PostTag).where(
            PostTag.deleted == False).where(
            PostTag.type == TagTypeEnum.POST_CAT).values(
            count=case(
                (PostTag.id == prev_category_id, PostTag.count - 1),
                (PostTag.id == post_category_id, PostTag.count + 1),
                else_=PostTag.count
            )
        )
        await session.execute(stmt)

    stmt = update(BlogPost).where(
        BlogPost.id == post.id).where(
        BlogPost.deleted == False).values(
        category_id=category.id
    )
    await session.execute(stmt)


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
        PostTag.id.in_(post.category_id for post in post_list)
    )
    category_dict = {cat.id: cat for cat in (await session.scalars(cat_stmt)).all()}
    return {post.id: category_dict.get(post.category_id) for post in post_list}


async def reset_category_count():
    async with new_session() as s:
        subquery = select(PostTag.id, func.count(BlogPost.id).label('category_count')).join(
            BlogPost, PostTag.id == BlogPost.category_id).where(
            PostTag.deleted == False).where(
            BlogPost.deleted == False).where(
            PostTag.type == TagTypeEnum.POST_CAT).where(
            BlogPost.status == PostStatusEnum.PUBLISHED
        ).group_by(PostTag.id).subquery()
        stmt = update(PostTag).where(PostTag.id == subquery.c.id).values(count=subquery.c.category_count)
        await s.execute(stmt)
