from wwricu.database.common import insert_all
from wwricu.database.relation import delete_post_tags, get_tag_ids_by_post_id
from wwricu.database.tag import update_tag_post_count, increase_post_tag_count, get_tags_by_ids
from wwricu.domain.entity import BlogPost, EntityRelation, PostTag
from wwricu.domain.enum import PostStatusEnum, RelationTypeEnum
from wwricu.domain.post import PostUpdateRO


async def update_tags(post: BlogPost, post_update: PostUpdateRO):
    tags = await get_tags_by_ids(post_update.tag_id_list)

    prev_tag_ids, post_tag_ids = set(), set()
    if post.status == PostStatusEnum.PUBLISHED:
        prev_tag_ids = {tag.id for tag in await get_post_tags(post)}
    if post_update.status == PostStatusEnum.PUBLISHED:
        post_tag_ids = set(post_update.tag_id_list)

    await update_tag_post_count(prev_tag_ids, post_tag_ids)
    await delete_post_tags(post.id)

    relations = [EntityRelation(src_id=post.id, dst_id=t.id, type=RelationTypeEnum.POST_TAG) for t in tags]
    await insert_all(relations)


async def update_tag_count(post: BlogPost, increment: int = 1):
    post_tags = await get_post_tags(post)
    await increase_post_tag_count([tag.id for tag in post_tags], increment)


async def get_post_tags(post: BlogPost) -> list[PostTag]:
    tag_ids = await get_tag_ids_by_post_id(post.id)
    return await get_tags_by_ids(tag_ids)
