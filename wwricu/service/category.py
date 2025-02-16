from sqlalchemy import select, update

from wwricu.domain.entity import BlogPost, PostCategory
from wwricu.service.database import session


async def get_category_by_id(category_id: int) -> PostCategory:
    stmt = select(PostCategory).where(
        PostCategory.deleted == False).where(
        PostCategory.id == category_id
    )
    return await session.scalar(stmt)


async def get_category_by_name(category_name: str) -> PostCategory | None:
    if category_name is None:
        return None
    stmt = select(PostCategory).where(
        PostCategory.deleted == False).where(
        PostCategory.name == category_name
    )
    return await session.scalar(stmt)


async def update_category(post: BlogPost, category_id: int | None = None) -> PostCategory | None:
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
    await session.flush()
    return category



async def get_post_category(post: BlogPost) -> PostCategory:
    stmt = select(PostCategory).where(
        PostCategory.deleted == False).where(
        PostCategory.id == post.category_id
    )
    return await session.scalar(stmt)


async def get_posts_category(post_list: list[BlogPost]) -> dict[int, PostCategory]:
    if not post_list:
        return dict()
    stmt = select(PostCategory).where(
        PostCategory.deleted == False).where(
        PostCategory.id.in_([post.category_id for post in post_list])
    )
    category_dict = {cat.id: cat for cat in (await session.scalars(stmt)).all()}
    return {post.id: category_dict.get(post.category_id) for post in post_list}
