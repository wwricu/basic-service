from wwricu.database.post import update_post_selective
from wwricu.database.tag import get_category, get_tags_by_example, update_category_post_count
from wwricu.domain.entity import BlogPost, PostTag
from wwricu.domain.enum import PostStatusEnum, TagTypeEnum
from wwricu.domain.post import PostUpdateRO
from wwricu.domain.tag import TagQueryDTO


async def update_category(post: BlogPost, post_update: PostUpdateRO):
    if (category := await get_category(category_id=post_update.category_id)) is None:
        return

    prev_category_id, post_category_id = None, None
    if post.status == PostStatusEnum.PUBLISHED:
        prev_category_id = post.category_id
    if post_update.status == PostStatusEnum.PUBLISHED:
        post_category_id = post_update.category_id

    await update_category_post_count(prev_category_id, post_category_id)
    await update_post_selective(post.id, category_id=category.id)


async def get_posts_category(post_list: list[BlogPost]) -> dict[int, PostTag]:
    if not post_list:
        return {}
    category_ids = [post.category_id for post in post_list if post.category_id]
    if not category_ids:
        return {}
    categories = await get_tags_by_example(TagQueryDTO(tag_ids=category_ids, type=TagTypeEnum.POST_CAT))
    category_dict = {cat.id: cat for cat in categories}
    return {post.id: category_dict.get(post.category_id) for post in post_list}
