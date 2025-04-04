import datetime

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from sqlalchemy import select, update

from wwricu.config import DatabaseConfig, Config
from wwricu.domain.common import ConfigRO, TrashBinRO, TrashBinVO
from wwricu.domain.enum import DatabaseActionEnum, EntityTypeEnum, TagTypeEnum
from wwricu.domain.entity import BlogPost, PostTag, SysConfig
from wwricu.service.database import database_restore, database_backup, session
from wwricu.service.security import admin_only

manage_api = APIRouter(prefix='/manage', tags=['Manage API'], dependencies=[Depends(admin_only)])


@manage_api.get('/trash/all', response_model=list[TrashBinVO])
async def trash_get_all() -> list[TrashBinVO]:
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


@manage_api.get('/trash/edit', response_model=list[TrashBinVO])
async def trash_edit(trash_bin: TrashBinRO):
    if trash_bin.deleted:
        pass
    else:
        pass


@manage_api.get('/database')
async def database(action: DatabaseActionEnum, background_task: BackgroundTasks):
    match action:
        case DatabaseActionEnum.RESTORE:
            background_task.add_task(database_restore)
        case DatabaseActionEnum.BACKUP:
            background_task.add_task(database_backup)
        case DatabaseActionEnum.DOWNLOAD:
            return FileResponse(DatabaseConfig.database, filename=DatabaseConfig.database)


@manage_api.post('/config/set')
async def config_set(config: ConfigRO):
    stmt = select(SysConfig).where(SysConfig.key == config.key).where(SysConfig.deleted == False)
    if await session.scalar(stmt) is None:
        session.add(SysConfig(key=config.key, value=config.value))
        return
    stmt = update(SysConfig).where(SysConfig.key == config.key).values(value=config.value)
    await session.execute(stmt)


@manage_api.get('/config/get', response_model=str | None)
async def config_get(key: str) -> str | None:
    stmt = select(SysConfig.value).where(SysConfig.key == key).where(SysConfig.deleted == False)
    return await session.scalar(stmt)
