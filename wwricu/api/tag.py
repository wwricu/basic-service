from fastapi import APIRouter, Depends

from wwricu.database.tag import get_tags_by_example, update_tag_selective
from wwricu.domain.tag import TagRO, TagVO, TagRequestRO, TagQueryDTO
from wwricu.component.cache import transient
from wwricu.function.common import reset_system_count
from wwricu.function.security import admin_only
from wwricu.function.tag import create_tag, update_tag_full

tag_api = APIRouter(prefix='/tag', tags=['Tag api'], dependencies=[Depends(admin_only), Depends(reset_system_count)])


@tag_api.post('/create', response_model=TagVO)
async def create_tag_api(tag_create: TagRO) -> TagVO:
    return await create_tag(tag_create)


@tag_api.post('/all', response_model=list[TagVO])
async def get_tags_api(get_tag: TagRequestRO) -> list[TagVO]:
    return [TagVO.model_validate(tag) for tag in await get_tags_by_example(TagQueryDTO(type=get_tag.type, page_index=get_tag.page_index, page_size=get_tag.page_size))]


@tag_api.post('/update', response_model=TagVO)
async def update_tag_api(tag_update: TagRO) -> TagVO:
    response = await update_tag_full(tag_update)
    await transient.delete_all()
    return response


@tag_api.get('/delete/{tag_id}', response_model=None)
async def delete_tag_api(tag_id: int):
    await update_tag_selective(tag_id, deleted=True)
    await transient.delete_all()
