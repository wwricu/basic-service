from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update, select

from wwricu.domain.common import HttpErrorDetail
from wwricu.domain.entity import PostTag, EntityRelation, BlogPost
from wwricu.domain.enum import TagTypeEnum, RelationTypeEnum
from wwricu.domain.input import TagRO, TagBatchRO
from wwricu.domain.output import TagVO
from wwricu.service.common import admin_only
from wwricu.service.database import session


tag_api = APIRouter(prefix='/tag', tags=['Tag Management'], dependencies=[Depends(admin_only)])


@tag_api.post('/create', response_model=TagVO)
async def create_tag(tag_create: TagRO) -> TagVO:
    tag = PostTag(
        name=tag_create.name,
        type=tag_create.type
    )
    session.add(tag)
    await session.flush()
    return TagVO.model_validate(tag)


@tag_api.post('/update', response_model=TagVO)
async def update_tag(tag_update: TagRO) -> TagVO:
    stmt = update(PostTag).where(PostTag.id == tag_update.id).values(name=tag_update.name)
    await session.execute(stmt)
    stmt = select(PostTag).where(PostTag.id == tag_update.id)
    return TagVO.model_validate(await session.scalar(stmt))


@tag_api.post('/delete', response_model=int)
async def delete_tags(tag_batch: TagBatchRO):
    post_stmt = update(PostTag).where(
        PostTag.type == tag_batch.type).where(
        PostTag.id.in_(tag_batch.id_list)).values(
        deleted=True
    )
    if tag_batch.type == TagTypeEnum.POST_TAG:
        tag_stmt = update(EntityRelation).where(
            EntityRelation.type == RelationTypeEnum.POST_TAG).where(
            EntityRelation.dst_id.in_(tag_batch.id_list)
        ).values(deleted=True)
    elif tag_batch.type == TagTypeEnum.POST_CAT:
        tag_stmt = update(BlogPost).where(BlogPost.category_id.in_(tag_batch.id_list)).values(category_id=None)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.INVALID_TAG_TYPE)
    result = await session.execute(post_stmt)
    await session.execute(tag_stmt)
    return result.rowcount
