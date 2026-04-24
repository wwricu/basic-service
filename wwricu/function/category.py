from wwricu.database.category import get_category_by_id, update_category_post_count, get_categories_by_ids
from wwricu.database.post import update_post_selective
from wwricu.domain.entity import BlogPost, PostTag
from wwricu.domain.enum import PostStatusEnum
from wwricu.domain.post import PostUpdateRO


async def update_category(post: BlogPost, post_update: PostUpdateRO):
    if (category := await get_category_by_id(post_update.category_id)) is None:
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
    categories = await get_categories_by_ids([post.category_id for post in post_list])
    category_dict = {cat.id: cat for cat in categories}
    return {post.id: category_dict.get(post.category_id) for post in post_list}
