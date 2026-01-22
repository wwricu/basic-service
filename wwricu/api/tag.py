from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy import update, select

from wwricu.domain.entity import PostTag
from wwricu.domain.tag import TagRO, TagVO
from wwricu.service.common import update_system_count
from wwricu.service.database import session
from wwricu.service.security import admin_only
from wwricu.service.tag import is_tag_exists

tag_api = APIRouter(prefix='/tag', tags=['Tag api'], dependencies=[Depends(admin_only), Depends(update_system_count)])


@tag_api.post('/create', response_model=TagVO)
async def create_tag(tag_create: TagRO) -> TagVO:
    if await is_tag_exists(tag_create.name, tag_create.type):
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f'{tag_create.type.name} {tag_create.name} already exists'
        )

    tag = PostTag(name=tag_create.name, type=tag_create.type)
    session.add(tag)
    await session.flush()
    return TagVO.model_validate(tag)


@tag_api.post('/update', response_model=TagVO)
async def update_tag(tag_update: TagRO) -> TagVO:
    stmt = select(PostTag).where(PostTag.id == tag_update.id)
    if (tag := await session.scalar(stmt)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=f'{tag_update.type} not found')

    if await is_tag_exists(tag.name, tag.type):
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=f'{tag.type.name} {tag.name} already exists')

    stmt = update(PostTag).where(PostTag.id == tag_update.id).values(name=tag_update.name)
    await session.execute(stmt)
    stmt = select(PostTag).where(PostTag.id == tag_update.id)
    return TagVO.model_validate(await session.scalar(stmt))


@tag_api.get('/delete/{tag_id}', response_model=None)
async def delete_tag(tag_id: int):
    stmt = update(PostTag).where(PostTag.id == tag_id).values(deleted=True)
    await session.execute(stmt)
