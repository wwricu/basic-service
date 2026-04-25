from fastapi import APIRouter, Depends

from wwricu.database import tag_db
from wwricu.domain.tag import TagRO, TagVO, TagRequestRO, TagQueryDTO
from wwricu.component.cache import transient
from wwricu.service import common_service, security_service, tag_service

tag_api = APIRouter(
    prefix='/tag',
    tags=['Tag api'],
    dependencies=[Depends(security_service.require_admin), Depends(common_service.init_public_counts)]
)


@tag_api.post('/create', response_model=TagVO)
async def create_tag_api(tag_create: TagRO) -> TagVO:
    return await tag_service.create_tag(tag_create)


@tag_api.post('/all', response_model=list[TagVO])
async def get_tags_api(get_tag: TagRequestRO) -> list[TagVO]:
    return [TagVO.model_validate(tag) for tag in await tag_db.get_by_criteria(TagQueryDTO(type=get_tag.type, page_index=get_tag.page_index, page_size=get_tag.page_size))]


@tag_api.post('/update', response_model=TagVO)
async def update_tag_api(tag_update: TagRO) -> TagVO:
    response = await tag_service.update_tag_full(tag_update)
    await transient.delete_all()
    return response


@tag_api.get('/delete/{tag_id}', response_model=None)
async def delete_tag_api(tag_id: int):
    await tag_db.update_selective(tag_id, deleted=True)
    await transient.delete_all()
