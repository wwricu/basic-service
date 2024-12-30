from sqlalchemy import delete, select

from wwricu.service.storage import delete_object
from wwricu.domain.entity import BlogPost, PostResource
from wwricu.domain.enum import PostResourceTypeEnum
from wwricu.service.database import session


async def get_post_by_id(post_id: int) -> BlogPost:
    stmt = select(BlogPost).where(BlogPost.id == post_id).where(BlogPost.deleted == False)
    return await session.scalar(stmt)


async def get_post_cover(post: BlogPost) -> PostResource:
    stmt = select(PostResource).where(
        PostResource.deleted == False).where(
        PostResource.type == PostResourceTypeEnum.COVER_IMAGE).where(
        PostResource.id == post.cover_id
    )
    return await session.scalar(stmt)


async def delete_post_cover(post: BlogPost) -> int:
    """HARD DELETE the resource because we are using free object storage"""
    stmt = select(PostResource).where(
        PostResource.deleted == False).where(
        PostResource.type == PostResourceTypeEnum.COVER_IMAGE).where(
        PostResource.id == post.cover_id
    )
    if (resource := await session.scalar(stmt)) is None:
        return 0
    delete_object(resource.key)
    stmt = delete(PostResource).where(PostResource.id == resource.id)
    result = await session.execute(stmt)
    return result.rowcount


async def clean_post_resource():
    """delete all unused files from oss"""
    pass
