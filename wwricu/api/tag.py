from fastapi import APIRouter, Depends

from wwricu.component.cache import query_cache
from wwricu.database import tag_db
from wwricu.domain.tag import TagRO, TagVO, TagRequestRO, TagQueryDTO
from wwricu.service import common_service, security_service, tag_service

tag_api = APIRouter(prefix='/tag', tags=['Tag api'], dependencies=[Depends(security_service.require_admin)])


@tag_api.post('/create', dependencies=[Depends(common_service.reset_sys_config)], response_model=TagVO)
async def create_tag_api(tag_create: TagRO) -> TagVO:
    response = await tag_service.create(tag_create)
    await query_cache.delete_all()
    return response


@tag_api.post('/all', response_model=list[TagVO])
async def get_tags_api(get_tag: TagRequestRO) -> list[TagVO]:
    return [TagVO.model_validate(tag) for tag in await tag_db.find_by_criteria(TagQueryDTO(type=get_tag.type, page_index=get_tag.page_index, page_size=get_tag.page_size))]


@tag_api.post('/update', dependencies=[Depends(common_service.reset_sys_config)], response_model=TagVO)
async def update_tag_api(tag_update: TagRO) -> TagVO:
    response = await tag_service.update_tag(tag_update)
    await query_cache.delete_all()
    return response


@tag_api.get('/delete/{tag_id}', dependencies=[Depends(common_service.reset_sys_config)], response_model=None)
async def delete_tag_api(tag_id: int):
    await tag_db.update_selective(tag_id, deleted=True)
    await query_cache.delete_all()
