from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Request, Response
from fastapi.responses import FileResponse

from wwricu.component.cache import query_cache
from wwricu.component.database import database_manager
from wwricu.config import app_config
from wwricu.domain.common import ConfigRO, TrashBinRO, TrashBinVO, UserRO
from wwricu.domain.enum import ConfigKeyEnum, DatabaseActionEnum, EntityTypeEnum
from wwricu.service import manage_service, post_service, security_service, tag_service

manage_api = APIRouter(prefix='/manage', tags=['Manage API'], dependencies=[Depends(security_service.require_admin)])


@manage_api.get('/trash/all', response_model=list[TrashBinVO])
async def trash_get_all_api() -> list[TrashBinVO]:
    return await manage_service.list_trash()


@manage_api.post('/trash/edit', response_model=None)
async def trash_edit_api(trash_bin: TrashBinRO):
    if trash_bin.type in (EntityTypeEnum.POST_IMAGE, EntityTypeEnum.POST_COVER):
        await post_service.process_resource_trash(trash_bin)
        return
    if trash_bin.type == EntityTypeEnum.BLOG_POST:
        await post_service.process_trash(trash_bin)
    else:
        await tag_service.process_trash(trash_bin)
    await query_cache.delete_all()


@manage_api.get('/database', response_model=None)
async def database_api(action: DatabaseActionEnum, background_task: BackgroundTasks):
    match action:
        case DatabaseActionEnum.RESTORE:
            background_task.add_task(database_manager.restore)
        case DatabaseActionEnum.BACKUP:
            background_task.add_task(database_manager.backup)
        case DatabaseActionEnum.DOWNLOAD:
            return FileResponse(app_config.database.database, filename=app_config.database.database)
    return None


@manage_api.post('/config/set', response_model=None)
async def config_set_api(config: ConfigRO):
    if config.value is None:
        await manage_service.delete_config([config.key])
        return
    await manage_service.set_config(config.key, config.value)


@manage_api.get('/config/get', response_model=str | None)
async def config_get_api(key: ConfigKeyEnum) -> str | None:
    if key in (ConfigKeyEnum.PASSWORD, ConfigKeyEnum.TOTP_SECRET):
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE)
    return await manage_service.get_config(key)


@manage_api.post('/user', response_model=None)
async def user_config_api(user: UserRO, request: Request, response: Response):
    await manage_service.update_admin_user(user)
    if user.username is not None or user.password is not None or user.reset is True:
        await security_service.logout(request, response)


@manage_api.get('/totp/enforce', response_model=str | None)
async def enforce_totp_secret_api(enforce: bool) -> str | None:
    return await manage_service.enforce_totp(enforce)


@manage_api.get('/totp/confirm', response_model=None)
async def totp_enforce_confirm_api(totp: str):
    await manage_service.confirm_totp(totp)
