from fastapi import APIRouter, Depends
from sqlalchemy import update, select

from wwricu.domain.entity import PostTag
from wwricu.domain.tag import TagRO, TagVO
from wwricu.service.common import update_system_count
from wwricu.service.database import session
from wwricu.service.security import admin_only

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


@tag_api.get('/delete/{tag_id}', response_model=None)
async def delete_tag(tag_id: int):
    stmt = update(PostTag).where(PostTag.id == tag_id).values(deleted=True)
    await session.execute(stmt)
