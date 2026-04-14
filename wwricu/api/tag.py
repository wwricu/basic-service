from fastapi import APIRouter, Depends, HTTPException, status as http_status

from wwricu.database.common import insert
from wwricu.database.tag import is_tag_exists, get_tag_by_id, update_tag_selective, get_tag_by_type
from wwricu.domain.entity import PostTag
from wwricu.domain.tag import TagRO, TagVO, TagRequestRO
from wwricu.component.cache import transient
from wwricu.service.common import reset_system_count
from wwricu.service.security import admin_only

tag_api = APIRouter(prefix='/tag', tags=['Tag api'], dependencies=[Depends(admin_only), Depends(reset_system_count)])


@tag_api.post('/create', response_model=TagVO)
async def create_tag_api(tag_create: TagRO) -> TagVO:
    if await is_tag_exists(tag_create.name, tag_create.type):
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f'{tag_create.type} {tag_create.name} already exists'
        )

    tag = PostTag(name=tag_create.name, type=tag_create.type)
    await insert(tag)
    await transient.delete_all()
    return TagVO.model_validate(tag)


@tag_api.post('/all', response_model=list[TagVO])
async def get_tags_api(get_tag: TagRequestRO) -> list[TagVO]:
    return [TagVO.model_validate(tag) for tag in await get_tag_by_type(get_tag)]


@tag_api.post('/update', response_model=TagVO)
async def update_tag_api(tag_update: TagRO) -> TagVO:
    if (tag := await get_tag_by_id(tag_update.id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=f'{tag_update.type} not found')
    if tag.name == tag_update.name:
        return TagVO.model_validate(tag)

    if await is_tag_exists(tag_update.name, tag_update.type):
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=f'{tag_update.type} {tag_update.name} already exists')
    tag.name = tag_update.name

    await update_tag_selective(tag_update.id, name=tag_update.name)
    await transient.delete_all()
    return TagVO.model_validate(tag)


@tag_api.get('/delete/{tag_id}', response_model=None)
async def delete_tag_api(tag_id: int):
    await update_tag_selective(tag_id, deleted=True)
    await transient.delete_all()
