from sqlalchemy import delete, select

from domain.entity import PostResource
from domain.enum import PostResourceTypeEnum
from service.storage import storage_delete
from wwricu.domain.entity import BlogPost
from wwricu.service.database import session


async def get_post_by_id(post_id: int) -> BlogPost:
    stmt = select(BlogPost).where(BlogPost.id == post_id).where(BlogPost.deleted == False)
    return await session.scalar(stmt)


async def get_post_cover(post_id: int) -> PostResource:
    stmt = select(PostResource).where(
        PostResource.deleted == False).where(
        PostResource.type == PostResourceTypeEnum.COVER_IMAGE).where(
        PostResource.post_id == post_id
    )
    return await session.scalar(stmt)


async def delete_post_cover(post_id: int) -> int:
    """HARD DELETE the resource because we are using free object storage"""
    stmt = select(PostResource).where(
        PostResource.deleted == False).where(
        PostResource.type == PostResourceTypeEnum.COVER_IMAGE).where(
        PostResource.post_id == post_id
    )
    resources = (await session.scalars(stmt)).all()
    if not resources:
        return 0
    for resource in resources:
        await storage_delete(resource.key)
    stmt = delete(PostResource).where(PostResource.id.in_(res.id for res in resources))
    result = await session.execute(stmt)
    return result.rowcount


async def clean_post_resource():
    pass
