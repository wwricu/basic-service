import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select

from wwricu.config import Config
from wwricu.domain.common import TrashBinVO, TrashBinRO
from wwricu.domain.enum import EntityTypeEnum, TagTypeEnum
from wwricu.domain.entity import BlogPost, PostTag
from wwricu.service.common import admin_only
from wwricu.service.database import session


manage_api = APIRouter(prefix='/manage', tags=['Manage API'], dependencies=[Depends(admin_only)])
trash_bin_api = APIRouter(prefix='/trash', tags=['Manage trash bin API'])
manage_api.include_router(trash_bin_api)

@manage_api.get('/all', dependencies=[Depends(admin_only)], response_model=list[TrashBinVO])
async def get_all() -> list[TrashBinVO]:
    result = []
    deadline = datetime.datetime.now() - datetime.timedelta(days=Config.trash_expire_day)
    stmt = select(BlogPost).where(BlogPost.deleted == True).where(BlogPost.update_time < deadline)
    deleted_post = (await session.scalars(stmt)).all()
    result.extend(TrashBinVO(
        id=post.id,
        name=post.title,
        type=EntityTypeEnum.BLOG_POST,
        status=post.status,
        deleted_time=post.update_time
    ) for post in deleted_post)
    stmt = select(PostTag).where(
        PostTag.deleted == True).where(
        PostTag.type.in_((TagTypeEnum.POST_CAT, EntityTypeEnum.POST_TAG))).where(
        PostTag.update_time < deadline
    )
    deleted_tag = (await session.scalars(stmt)).all()
    result.extend(TrashBinVO(
        id=tag.id,
        name=tag.name,
        type=EntityTypeEnum.POST_TAG if tag.type == TagTypeEnum.POST_TAG else EntityTypeEnum.POST_CAT,
        deleted_time=tag.update_time
    ) for tag in deleted_tag)
    sorted(result, key=lambda item: item.deleted_time, reverse=True)
    return result


@manage_api.get('/edit', dependencies=[Depends(admin_only)], response_model=list[TrashBinVO])
async def edit(trash_bin: TrashBinRO):
    if trash_bin.deleted:
        pass
    else:
        pass
