from loguru import logger as log
from sqlalchemy import delete, select

from wwricu.domain.post import PostDetailVO, PostResourceVO
from wwricu.domain.tag import TagVO
from wwricu.domain.entity import BlogPost, PostResource
from wwricu.domain.enum import PostResourceTypeEnum
from wwricu.service.category import get_post_category, get_posts_category
from wwricu.service.database import get_session, session
from wwricu.service.storage import delete_object, delete_objects, list_all_objects
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
    async with get_session() as s:
        resource_keys = await s.scalars(select(PostResource.key))
        resource_keys = set(resource_keys.all())
        all_s3_objects = list_all_objects()
        keys_to_del = list(filter(lambda key: key not in resource_keys, map(lambda r: r.Key, all_s3_objects)))
        log.warning(f'{len(keys_to_del)} objects to be deleted')
        delete_objects(keys_to_del)


async def get_post_detail(blog_post: BlogPost) -> PostDetailVO:
    # TODO: optimize with join
    category = await get_post_category(blog_post)
    tags = await get_post_tags(blog_post)
    cover = await get_post_cover(blog_post)
    post_detail = PostDetailVO.model_validate(blog_post)
    post_detail.tag_list = list(map(TagVO.model_validate, tags))
    if category is not None:
        post_detail.category = TagVO.model_validate(category)
    if cover is not None:
        post_detail.cover = PostResourceVO.model_validate(cover)
    return post_detail


async def get_posts_cover(post_list: list[BlogPost]) -> dict[int, PostResource]:
    stmt = select(PostResource, BlogPost.id).join(
        BlogPost, PostResource.id == BlogPost.cover_id).where(
        PostResource.deleted == False).where(
        PostResource.type == PostResourceTypeEnum.COVER_IMAGE).where(
        BlogPost.deleted == False).where(
        BlogPost.id.in_(post.id for post in post_list)
    )
    result = await session.execute(stmt)
    return {post_id: cover for cover, post_id in result.all()}


async def get_posts_preview(post_list: list[BlogPost]) -> list[PostDetailVO]:
    categories = await get_posts_category(post_list)
    tags = await get_posts_tag_lists(post_list)
    covers = await get_posts_cover(post_list)
    def generator(post: BlogPost) -> PostDetailVO:
        detail = PostDetailVO.model_validate(post)
        if category := categories.get(post.id):
            detail.category = TagVO.model_validate(category)
        detail.tag_list = [TagVO.model_validate(tag) for tag in tags.get(post.id, [])]
        if cover := covers.get(post.id):
            detail.cover = PostResourceVO.model_validate(cover)
        return detail
    return list(map(generator, post_list))