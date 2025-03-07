import asyncio

from sqlalchemy import delete, select

from wwricu.domain.output import PostDetailVO, TagVO, PostResourceVO
from wwricu.service.storage import delete_object
from wwricu.domain.entity import BlogPost, PostResource
from wwricu.domain.enum import PostResourceTypeEnum
from wwricu.service.category import get_post_category, get_posts_category
from wwricu.service.database import session
from wwricu.service.tag import get_post_tags, get_posts_tag_lists


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


async def get_post_detail(blog_post: BlogPost) -> PostDetailVO:
    # TODO: optimize with join
    category, tags, cover = await asyncio.gather(
        get_post_category(blog_post),
        get_post_tags(blog_post),
        get_post_cover(blog_post)
    )
    post_detail = PostDetailVO.model_validate(blog_post)
    post_detail.tag_list = [TagVO.model_validate(tag) for tag in tags]
    if category is not None:
        post_detail.category = TagVO.model_validate(category)
    if cover is not None:
        post_detail.cover = PostResourceVO.model_validate(cover)
    return post_detail


async def get_posts_preview(post_list: list[BlogPost]) -> list[PostDetailVO]:
    categories, tags = await asyncio.gather(
        get_posts_category(post_list),
        get_posts_tag_lists(post_list)
    )
    result = []
    for post in post_list:
        detail = PostDetailVO.model_validate(post)
        if category := categories.get(post.id):
            detail.category = TagVO.model_validate(category)
        detail.tag_list = [TagVO.model_validate(tag) for tag in tags.get(post.id, [])]
        result.append(detail)
    return result
