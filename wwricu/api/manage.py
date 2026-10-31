from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, status, Request, Response
from fastapi.responses import FileResponse

from wwricu.component.cache import query_cache
from wwricu.config import app_config
from wwricu.domain.common import ConfigRO, TrashBinRO, TrashBinVO, UserRO
from wwricu.domain.enum import ConfigKeyEnum, DatabaseActionEnum, EntityTypeEnum
from wwricu.service import common_service, manage_service, post_service, security_service, tag_service

manage_api = APIRouter(prefix='/admin/manage', tags=['Manage API'], dependencies=[Depends(security_service.require_admin)])


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
async def database_download_api():
    return FileResponse(app_config.database.name, filename=app_config.database.name)


@manage_api.post('/database', response_model=None)
async def database_api(background_task: BackgroundTasks, action: DatabaseActionEnum = Body(embed=True)):
    match action:
        case DatabaseActionEnum.RESTORE:
            background_task.add_task(common_service.restore_database)
        case DatabaseActionEnum.BACKUP:
            background_task.add_task(common_service.backup_database)
        case DatabaseActionEnum.DOWNLOAD:
            raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE)


@manage_api.post('/config/set', response_model=None)
async def config_set_api(config: ConfigRO):
    # White list, all other keys shall be set via their dedicated apis
    if config.key not in ConfigKeyEnum.api_set_white_list():
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE)
    if config.value is None:
        await manage_service.delete_config([config.key])
        return
    await manage_service.set_config(config.key, config.value)


@manage_api.get('/config/get', response_model=str | None)
async def config_get_api(key: ConfigKeyEnum) -> str | None:
    if key in ConfigKeyEnum.api_get_black_list():
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE)
    return await manage_service.get_config(key)


@manage_api.post('/user', response_model=None)
async def user_config_api(user: UserRO, request: Request, response: Response):
    await manage_service.update_admin_user(user)
    if user.username is not None or user.password is not None or user.reset is True:
        await security_service.logout(request, response)


@manage_api.post('/totp/enforce', response_model=str | None)
async def enforce_totp_secret_api(enforce: bool = Body(embed=True)) -> str | None:
    return await manage_service.enforce_totp(enforce)


@manage_api.post('/totp/confirm', response_model=None)
async def totp_enforce_confirm_api(totp: str = Body(embed=True)):
    await manage_service.confirm_totp(totp)
