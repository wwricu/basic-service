from fastapi import HTTPException, status as http_status

from wwricu.database.common import insert, insert_all
from wwricu.database.relation import delete_post_tags, get_tag_ids_by_post_id
from wwricu.database.tag import is_tag_exists, get_tag_by_id, update_tag_selective, update_tag_post_count, increase_post_tag_count, get_tags_by_ids
from wwricu.domain.entity import BlogPost, EntityRelation, PostTag
from wwricu.domain.enum import PostStatusEnum, RelationTypeEnum
from wwricu.domain.post import PostUpdateRO
from wwricu.domain.tag import TagRO, TagVO
from wwricu.component.cache import transient


async def create_tag(tag_create: TagRO) -> TagVO:
    if await is_tag_exists(tag_create.name, tag_create.type):
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f'{tag_create.type} {tag_create.name} already exists'
        )
    tag = PostTag(name=tag_create.name, type=tag_create.type)
    await insert(tag)
    await transient.delete_all()
    return TagVO.model_validate(tag)


async def update_tag_full(tag_update: TagRO) -> TagVO:
    tag = await get_tag_by_id(tag_update.id)
    if tag is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=f'{tag_update.type} not found')
    if tag.name == tag_update.name:
        return TagVO.model_validate(tag)
    if await is_tag_exists(tag_update.name, tag_update.type):
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=f'{tag_update.type} {tag_update.name} already exists')
    tag.name = tag_update.name
    await update_tag_selective(tag_update.id, name=tag_update.name)
    await transient.delete_all()
    return TagVO.model_validate(tag)


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
