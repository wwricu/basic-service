import datetime
import re

import bcrypt
import pyotp
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy import select, update, delete

from wwricu.config import DatabaseConfig, Config
from wwricu.domain.common import ConfigRO, TrashBinRO, TrashBinVO, UserRO
from wwricu.domain.constant import CommonConstant, HttpErrorDetail
from wwricu.domain.enum import DatabaseActionEnum, EntityTypeEnum, TagTypeEnum, ConfigKeyEnum
from wwricu.domain.entity import BlogPost, PostTag
from wwricu.service.cache import cache
from wwricu.service.database import database_restore, database_backup, session
from wwricu.service.manage import set_config, get_config, delete_config
from wwricu.service.security import admin_only

manage_api = APIRouter(prefix='/manage', tags=['Manage API'], dependencies=[Depends(admin_only)])


@manage_api.get('/trash/all', response_model=list[TrashBinVO])
async def trash_get_all() -> list[TrashBinVO]:
    deadline = datetime.datetime.now() - datetime.timedelta(days=Config.trash_expire_day)
    stmt = select(BlogPost).where(BlogPost.deleted == True).where(BlogPost.update_time > deadline)
    deleted_post = (await session.scalars(stmt)).all()
    deleted_post = [TrashBinVO(
        id=post.id,
        name=post.title,
        type=EntityTypeEnum.BLOG_POST,
        status=post.status,
        delete_time=post.update_time
    ) for post in deleted_post]
    stmt = select(PostTag).where(
        PostTag.deleted == True).where(
        PostTag.type.in_((TagTypeEnum.POST_CAT, EntityTypeEnum.POST_TAG))).where(
        PostTag.update_time > deadline
    )
    deleted_tag = (await session.scalars(stmt)).all()
    deleted_tag = [TrashBinVO(
        id=tag.id,
        name=tag.name,
        type=EntityTypeEnum.POST_TAG if tag.type == TagTypeEnum.POST_TAG else EntityTypeEnum.POST_CAT,
        delete_time=tag.update_time
    ) for tag in deleted_tag]
    result = deleted_post + deleted_tag
    sorted(result, key=lambda item: item.delete_time, reverse=True)
    return result


@manage_api.post('/trash/edit', response_model=None)
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
    stmt = delete(entity).where(entity.deleted == True) if trash_bin.delete else update(entity).values(deleted=False)
    await session.execute(stmt.where(entity.id == trash_bin.id))


@manage_api.get('/database', response_model=None)
async def database(action: DatabaseActionEnum, background_task: BackgroundTasks):
    match action:
        case DatabaseActionEnum.RESTORE:
            background_task.add_task(database_restore)
        case DatabaseActionEnum.BACKUP:
            background_task.add_task(database_backup)
        case DatabaseActionEnum.DOWNLOAD:
            return FileResponse(DatabaseConfig.database, filename=DatabaseConfig.database)
    return None


@manage_api.post('/config/set', response_model=None)
async def config_set(config: ConfigRO):
    # Set None to delete config
    value = config.value
    if value is None:
        await delete_config([config.key])
        return
    await set_config(config.key, config.value)


@manage_api.get('/config/get', response_model=str | None)
async def config_get(key: str) -> str | None:
    if key == ConfigKeyEnum.TOTP_SECRET:
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=HttpErrorDetail.CONFIG_NOT_ALLOWED)
    return await get_config(ConfigKeyEnum(key))


@manage_api.post('/user', response_model=None)
async def user_config(user: UserRO, request: Request):
    if user.username is not None:
        if len(user.username) < 3 or not bool(re.match('^[a-zA-Z][a-zA-Z0-9_-]*$', user.username)):
            raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, 'Invalid username')
        await set_config(ConfigKeyEnum.USERNAME, user.username)
    if user.password is not None:
        if len(user.password) < 8 or user.password.isalnum():
            raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, 'Invalid password')
        password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
        await set_config(ConfigKeyEnum.PASSWORD, password)
    if user.reset is True:
        await delete_config([ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD])
    if user.username is not None or user.password is not None or user.reset is True:
        session_id = request.cookies.get(CommonConstant.SESSION_ID)
        await cache.delete(session_id)


@manage_api.get('/totp/enforce', response_model=str | None)
async def enforce_totp_secret(enforce: bool) -> str | None:
    if not enforce:
        await delete_config([ConfigKeyEnum.TOTP_ENFORCE, ConfigKeyEnum.TOTP_SECRET])
        return None
    secret = pyotp.random_base32()
    await set_config(ConfigKeyEnum.TOTP_SECRET, secret)
    return secret


@manage_api.get('/totp/confirm')
async def totp_enforce_confirm(totp: str):
    secret = await get_config(ConfigKeyEnum.TOTP_SECRET)
    if secret is None:
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=HttpErrorDetail.NO_TOTP_SECRET)
    totp_client = pyotp.TOTP(secret)
    if not totp_client.verify(totp, valid_window=1):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_TOTP)
    await set_config(ConfigKeyEnum.TOTP_ENFORCE, str(True))
