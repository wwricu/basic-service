from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy import update, select, desc

from wwricu.domain.entity import PostTag
from wwricu.domain.tag import TagRO, TagVO, TagRequestRO
from wwricu.service.cache import transient
from wwricu.service.common import update_system_count
from wwricu.service.database import session, on_api_commit
from wwricu.service.security import admin_only
from wwricu.service.tag import is_tag_exists

tag_api = APIRouter(prefix='/tag', tags=['Tag api'], dependencies=[Depends(admin_only), Depends(update_system_count)])


@tag_api.post('/create', response_model=TagVO)
async def create_tag(tag_create: TagRO) -> TagVO:
    if await is_tag_exists(tag_create.name, tag_create.type):
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f'{tag_create.type} {tag_create.name} already exists'
        )

    tag = PostTag(name=tag_create.name, type=tag_create.type)
    session.add(tag)
    await session.flush()
    on_api_commit(transient.delete_all())
    return TagVO.model_validate(tag)


@tag_api.post('/all', response_model=list[TagVO])
async def get_tags(get_tag: TagRequestRO) -> list[TagVO]:
    stmt = select(PostTag).where(
        PostTag.deleted == False).where(
        PostTag.type == get_tag.type).order_by(
        desc(PostTag.create_time)
    )
    if get_tag.page_index > 0 and get_tag.page_size > 0:
        stmt = stmt.limit(get_tag.page_size).offset((get_tag.page_index - 1) * get_tag.page_size)
    return [TagVO.model_validate(tag) for tag in (await session.scalars(stmt)).all()]


@tag_api.post('/update', response_model=TagVO)
async def update_tag(tag_update: TagRO) -> TagVO:
    stmt = select(PostTag).where(PostTag.id == tag_update.id)
    if (tag := await session.scalar(stmt)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=f'{tag_update.type} not found')
    if tag.name == tag_update.name:
        return TagVO.model_validate(tag)

    if await is_tag_exists(tag_update.name, tag_update.type):
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=f'{tag_update.type} {tag_update.name} already exists')
    tag.name = tag_update.name

    stmt = update(PostTag).where(PostTag.id == tag_update.id).values(name=tag_update.name)
    await session.execute(stmt)
    on_api_commit(transient.delete_all())
    return TagVO.model_validate(tag)


@tag_api.get('/delete/{tag_id}', response_model=None)
async def delete_tag(tag_id: int):
    stmt = update(PostTag).where(PostTag.id == tag_id).values(deleted=True)
    await session.execute(stmt)
    on_api_commit(transient.delete_all())

