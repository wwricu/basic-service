from sqlalchemy import select, update

from wwricu.component.database import get_session
from wwricu.domain.entity import BlogPost, PostResource
from wwricu.domain.enum import PostResourceTypeEnum


async def find_by_id(resource_id: int, resource_type: PostResourceTypeEnum | None = None, deleted: bool = False) -> PostResource | None:
    stmt = select(PostResource).where(PostResource.deleted == deleted).where(PostResource.id == resource_id)
    if resource_type is not None:
        stmt = stmt.where(PostResource.type == resource_type)
    async with get_session() as s:
        return await s.scalar(stmt)


async def delete_resources(keys: list[str]):
    stmt = update(PostResource).where(PostResource.key.in_(keys)).values(deleted=True)
    async with get_session() as s:
        await s.execute(stmt)


async def delete_post_resources(post_id: int):
    stmt = update(PostResource).where(PostResource.post_id == post_id).values(deleted=True)
    async with get_session() as s:
        await s.execute(stmt)


async def find_posts_cover(post_list: list[BlogPost]) -> dict[int, PostResource]:
    if not post_list:
        return {}
    stmt = select(PostResource, BlogPost.id).join(
        BlogPost, PostResource.id == BlogPost.cover_id).where(
        PostResource.deleted == False).where(
        PostResource.type == PostResourceTypeEnum.COVER_IMAGE).where(
        BlogPost.deleted == False).where(
        BlogPost.id.in_(post.id for post in post_list)
    )
    async with get_session() as s:
        result = await s.execute(stmt)
    return {post_id: cover for cover, post_id in result.all()}


async def find_deleted_resource() -> list[PostResource]:
    stmt = select(PostResource).where(PostResource.deleted == True)
    async with get_session() as s:
        return list((await s.scalars(stmt)).all())


async def find_post_covers(post_id: int) -> list[PostResource]:
    stmt = select(PostResource).where(PostResource.post_id == post_id).where(PostResource.deleted == False)
    async with get_session() as s:
        return list((await s.scalars(stmt)).all())
