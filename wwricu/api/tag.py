from fastapi import APIRouter, Depends
from sqlalchemy import update, select

from wwricu.domain.entity import PostTag, EntityRelation
from wwricu.domain.enum import RelationTypeEnum
from wwricu.domain.input import TagRO
from wwricu.domain.output import TagVO
from wwricu.service.common import admin_only
from wwricu.service.database import session


tag_api = APIRouter(prefix='/tag', tags=['Tag Management'], dependencies=[Depends(admin_only)])


@tag_api.post('/create', response_model=TagVO)
async def create_tag(tag_create: TagRO) -> TagVO:
    tag = PostTag(name=tag_create.name, description=tag_create.description)
    session.add(tag)
    await session.flush()
    return TagVO.model_validate(tag)


@tag_api.post('/update', response_model=TagVO)
async def update_tag(tag_update: TagRO) -> TagVO:
    stmt = update(PostTag).where(PostTag.id == tag_update.id).values(
        name=tag_update.name,
        description=tag_update.description
    )
    await session.execute(stmt)
    stmt = select(PostTag).where(PostTag.id == tag_update.id)
    return TagVO.model_validate(await session.scalar(stmt))


@tag_api.post('/delete/{tag_id}', response_model=int)
async def delete_tag(tag_id: int) -> int:
    post_stmt = update(PostTag).where(PostTag.id == tag_id).values(deleted=True)
    tag_stmt = update(EntityRelation).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.dst_id == tag_id
    ).values(deleted=True)
    result = await session.execute(post_stmt)
    await session.execute(tag_stmt)
    return result.rowcount
