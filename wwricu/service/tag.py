from fastapi import HTTPException, status as http_status

from wwricu.database import common_db, tag_db
from wwricu.domain.common import TrashBinRO
from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.entity import PostTag
from wwricu.domain.tag import TagRO, TagVO, TagQueryDTO


async def create(tag_create: TagRO) -> TagVO:
    if await tag_db.count(TagQueryDTO(name=tag_create.name, type=tag_create.type)) > 0:
        raise HTTPException(http_status.HTTP_409_CONFLICT, f'{tag_create.type} {tag_create.name} already exists')
    tag = PostTag(name=tag_create.name, type=tag_create.type)
    await common_db.insert(tag)
    return TagVO.model_validate(tag)


async def update(tag_update: TagRO) -> TagVO:
    if tag_update.id is None:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, detail=HttpErrorDetail.INVALID_VALUE)
    if not (tags := await tag_db.find_by_criteria(TagQueryDTO(tag_ids=[tag_update.id]))) or (tag := tags[0]) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=f'{tag_update.type} not found')
    if tag.name == tag_update.name:
        return TagVO.model_validate(tag)
    if await tag_db.count(TagQueryDTO(name=tag_update.name, type=tag_update.type)) > 0:
        raise HTTPException(http_status.HTTP_409_CONFLICT, f'{tag_update.type} {tag_update.name} already exists')
    tag.name = tag_update.name
    await tag_db.update_selective(tag_update.id, name=tag_update.name)
    return TagVO.model_validate(tag)


async def process_trash(trash_bin: TrashBinRO):
    if trash_bin.delete:
        await common_db.hard_delete(PostTag, trash_bin.id)
    else:
        await common_db.recover(PostTag, trash_bin.id)
