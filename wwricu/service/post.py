from wwricu.database.category import get_category_by_id
from wwricu.database.post import get_posts_by_example, get_posts_count
from wwricu.database.resource import get_post_cover, delete_resource, get_posts_cover
from wwricu.database.tag import get_tags_by_posts
from wwricu.domain.common import PageVO
from wwricu.domain.enum import PostStatusEnum
from wwricu.domain.post import PostDetailVO, PostResourceVO, PostQueryDTO
from wwricu.domain.tag import TagVO
from wwricu.domain.entity import BlogPost
from wwricu.service.category import get_posts_category
from wwricu.component.storage import oss_public
from wwricu.service.tag import get_post_tags


async def get_posts_by_query(query: PostQueryDTO) -> PageVO[PostDetailVO]:
    posts = await get_posts_by_example(query)
    return PageVO[PostDetailVO](
        page_size=query.page_size,
        page_index=query.page_index,
        count=await get_posts_count(query),
        data=await get_posts_preview(posts)
    )


async def delete_post_cover(post: BlogPost):
    """HARD DELETE the resource because we are using free object storage"""
    if (resource := await get_post_cover(post.cover_id)) is None:
        return
    await delete_resource(resource.id)
    oss_public.delete(resource.key)


async def get_post_detail(blog_post: BlogPost) -> PostDetailVO:
    category = await get_category_by_id(blog_post.category_id)
    tags = await get_post_tags(blog_post)
    cover = await get_post_cover(blog_post.cover_id)
    post_detail = PostDetailVO.model_validate(blog_post)
    post_detail.tag_list = list(map(TagVO.model_validate, tags))

    if category is not None:
        post_detail.category = TagVO.model_validate(category)
    if cover is not None:
        post_detail.cover = PostResourceVO.model_validate(cover)
    return post_detail


async def get_posts_preview(post_list: list[BlogPost]) -> list[PostDetailVO]:
    """Generate post preview from BlogPost list"""
    categories = await get_posts_category(post_list)
    tags = await get_tags_by_posts(post_list)
    covers = await get_posts_cover(post_list)

    def generator(post: BlogPost) -> PostDetailVO:
        detail = PostDetailVO(
            id=post.id,
            title=post.title,
            preview=post.preview,
            tag_list=[TagVO.model_validate(tag) for tag in tags.get(post.id, [])],
            status=PostStatusEnum(post.status),
            create_time=post.create_time,
            update_time=post.update_time
        )
        if category := categories.get(post.id):
            detail.category = TagVO.model_validate(category)
        if cover := covers.get(post.id):
            detail.cover = PostResourceVO.model_validate(cover)
        return detail

    return list(map(generator, post_list))
