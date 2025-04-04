import datetime

import bcrypt
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import FileResponse, Response
from sqlalchemy import select, update, delete

from wwricu.config import DatabaseConfig, Config
from wwricu.domain.common import ConfigRO, TrashBinRO, TrashBinVO, UserRO
from wwricu.domain.constant import CommonConstant, HttpErrorDetail
from wwricu.domain.enum import DatabaseActionEnum, EntityTypeEnum, TagTypeEnum, ConfigKeyEnum
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
    match trash_bin.type:
        case EntityTypeEnum.BLOG_POST:
            entity = BlogPost
        case EntityTypeEnum.POST_CAT:
            entity = PostTag
        case EntityTypeEnum.POST_TAG:
            entity = PostTag
        case _:
            raise HTTPException(status.HTTP_404_NOT_FOUND, HttpErrorDetail.UNKNOWN_ENTITY_TYPE)
    stmt = delete(entity).where(entity.deleted == True) if trash_bin.deleted else update(entity).values(deleted=False)
    await session.execute(stmt.where(entity.id == trash_bin.id))


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


@manage_api.post('/admin')
async def admin(user: UserRO, response: Response):
    if user.username is not None:
        stmt = delete(SysConfig).where(SysConfig.key == ConfigKeyEnum.USERNAME)
        await session.execute(stmt)
        session.add(SysConfig(key=ConfigKeyEnum.USERNAME, value=user.username))
    if user.password is not None:
        stmt = delete(SysConfig).where(SysConfig.key == ConfigKeyEnum.PASSWORD)
        await session.execute(stmt)
        password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
        session.add(SysConfig(key=ConfigKeyEnum.PASSWORD, value=password))
    if user.reset is True:
        stmt = delete(SysConfig).where(SysConfig.key.in_((ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD)))
        await session.execute(stmt)
    if user.username is not None or user.password is not None or user.reset is True:
        response.delete_cookie(CommonConstant.SESSION_ID, secure=True, httponly=True, samesite='lax')
        response.delete_cookie(CommonConstant.COOKIE_SIGN, secure=True, httponly=True, samesite='lax')
