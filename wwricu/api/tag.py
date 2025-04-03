from fastapi import APIRouter, Depends
from sqlalchemy import update, select

from wwricu.domain.entity import BlogPost, PostTag
from wwricu.domain.enum import TagTypeEnum
from wwricu.domain.tag import TagRO, TagVO
from wwricu.service.common import admin_only, update_system_count
from wwricu.service.database import session

tag_api = APIRouter(prefix='/tag', tags=['Tag api'], dependencies=[Depends(admin_only), Depends(update_system_count)])


@tag_api.post('/create', response_model=TagVO)
async def create_tag(tag_create: TagRO) -> TagVO:
    tag = PostTag(name=tag_create.name, type=tag_create.type)
    session.add(tag)
    await session.flush()
    return TagVO.model_validate(tag)


@tag_api.post('/update', response_model=TagVO)
async def update_tag(tag_update: TagRO) -> TagVO:
    stmt = update(PostTag).where(PostTag.id == tag_update.id).values(name=tag_update.name)
    await session.execute(stmt)
    stmt = select(PostTag).where(PostTag.id == tag_update.id)
    return TagVO.model_validate(await session.scalar(stmt))


@tag_api.get('/delete/{tag_id}', response_model=int)
async def delete_tag(tag_id: int) -> int:
    stmt = select(PostTag).where(PostTag.deleted == False).where(PostTag.id == tag_id)
    tag = await session.scalar(stmt)
    if tag.type == TagTypeEnum.POST_CAT:
        stmt = update(BlogPost).where(BlogPost.category_id == tag_id).values(category_id=None)
        await session.execute(stmt)
    stmt = update(PostTag).where(PostTag.id == tag_id).values(deleted=True)
    result = await session.execute(stmt)
    return result.rowcount
