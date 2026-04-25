from sqlalchemy import delete, select

from wwricu.component.database import get_session
from wwricu.domain.entity import BlogPost, PostResource, EntityRelation
from wwricu.domain.enum import PostResourceTypeEnum, RelationTypeEnum


async def get_post_cover(resource_id: int) -> PostResource | None:
    stmt = select(PostResource).where(
        PostResource.deleted == False).where(
        PostResource.type == PostResourceTypeEnum.COVER_IMAGE).where(
        PostResource.id == resource_id
    )
    async with get_session() as s:
        return await s.scalar(stmt)


async def delete_resource(resource_id: int):
    stmt = delete(PostResource).where(PostResource.id == resource_id)
    async with get_session() as s:
        await s.execute(stmt)


async def get_posts_cover(post_list: list[BlogPost]) -> dict[int, PostResource]:
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


async def cleanup_unlinked_resources() -> list[PostResource]:
    linked = select(EntityRelation.dst_id).where(
        EntityRelation.deleted == False).where(
        EntityRelation.type == RelationTypeEnum.POST_RES
    ).distinct()
    select_stmt = select(PostResource).where(PostResource.deleted == False).where(PostResource.id.notin_(linked))

    async with get_session() as s:
        deleted_resources = list((await s.scalars(select_stmt)).all())
        delete_stmt = delete(PostResource).where(PostResource.id.in_((r.id for r in deleted_resources)))
        await s.execute(delete_stmt)

    return deleted_resources
