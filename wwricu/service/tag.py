from fastapi import HTTPException, status as http_status

import wwricu.database as db
from wwricu.database import post_db, tag_db
from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.entity import BlogPost, EntityRelation, PostTag
from wwricu.domain.enum import PostStatusEnum, RelationTypeEnum, TagTypeEnum
from wwricu.domain.post import PostUpdateRO
from wwricu.domain.tag import TagRO, TagVO, TagQueryDTO


async def create(tag_create: TagRO) -> TagVO:
    if await tag_db.count(TagQueryDTO(name=tag_create.name, type=tag_create.type)) > 0:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f'{tag_create.type} {tag_create.name} already exists'
        )
    tag = PostTag(name=tag_create.name, type=tag_create.type)
    await db.insert(tag)
    return TagVO.model_validate(tag)


async def update_tag(tag_update: TagRO) -> TagVO:
    if tag_update.id is None:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, detail=HttpErrorDetail.INVALID_VALUE)
    if not (tags := await tag_db.get_by_criteria(TagQueryDTO(tag_ids=[tag_update.id]))) or (tag := tags[0]) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=f'{tag_update.type} not found')
    if tag.name == tag_update.name:
        return TagVO.model_validate(tag)
    if await tag_db.count(TagQueryDTO(name=tag_update.name, type=tag_update.type)) > 0:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=f'{tag_update.type} {tag_update.name} already exists')
    tag.name = tag_update.name
    await tag_db.update_selective(tag_update.id, name=tag_update.name)
    return TagVO.model_validate(tag)


async def update_post_tags(post: BlogPost, post_update: PostUpdateRO):
    tags = await tag_db.get_by_criteria(TagQueryDTO(tag_ids=post_update.tag_id_list, type=TagTypeEnum.POST_TAG))

    prev_tag_ids, post_tag_ids = set(), set()
    if post.status == PostStatusEnum.PUBLISHED:
        prev_tag_ids = {tag.id for tag in await get_post_tags(post)}
    if post_update.status == PostStatusEnum.PUBLISHED:
        post_tag_ids = set(post_update.tag_id_list)

    await tag_db.update_tag_post_count(prev_tag_ids, post_tag_ids)
    await tag_db.delete_post_tags(post.id)

    relations = [EntityRelation(src_id=post.id, dst_id=t.id, type=RelationTypeEnum.POST_TAG) for t in tags]
    await db.insert_all(relations)


async def update_tag_count(post: BlogPost, increment: int = 1):
    post_tags = await get_post_tags(post)
    await tag_db.increase_post_tag_count([tag.id for tag in post_tags], increment)


async def get_post_tags(post: BlogPost) -> list[PostTag]:
    tag_ids = await tag_db.get_tag_ids_by_post_id(post.id)
    return await tag_db.get_by_criteria(TagQueryDTO(tag_ids=tag_ids, type=TagTypeEnum.POST_TAG))


async def update_category(post: BlogPost, post_update: PostUpdateRO):
    if (category := await tag_db.get_category(category_id=post_update.category_id)) is None:
        return

    prev_category_id, post_category_id = None, None
    if post.status == PostStatusEnum.PUBLISHED:
        prev_category_id = post.category_id
    if post_update.status == PostStatusEnum.PUBLISHED:
        post_category_id = post_update.category_id

    await tag_db.update_category_post_count(prev_category_id, post_category_id)
    await post_db.update_selective(post.id, category_id=category.id)


async def get_posts_category(post_list: list[BlogPost]) -> dict[int, PostTag]:
    if not post_list:
        return {}
    category_ids = [post.category_id for post in post_list if post.category_id]
    if not category_ids:
        return {}
    categories = await tag_db.get_by_criteria(TagQueryDTO(tag_ids=category_ids, type=TagTypeEnum.POST_CAT))
    category_dict = {cat.id: cat for cat in categories}
    return {post.id: tag for post in post_list if (tag := category_dict.get(post.category_id))}
