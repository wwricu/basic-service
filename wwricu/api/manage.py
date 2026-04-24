from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from wwricu.config import DatabaseConfig
from wwricu.component.database import database_restore, database_backup
from wwricu.domain.common import ConfigRO, TrashBinRO, TrashBinVO, UserRO
from wwricu.domain.constant import CommonConstant, HttpErrorDetail
from wwricu.domain.enum import ConfigKeyEnum, DatabaseActionEnum
from wwricu.function.manage import confirm_totp, delete_config, enforce_totp, get_config, get_trash_list, set_config, update_trash, update_user_config
from wwricu.function.security import admin_only

manage_api = APIRouter(prefix='/manage', tags=['Manage API'], dependencies=[Depends(admin_only)])


@manage_api.get('/trash/all', response_model=list[TrashBinVO])
async def trash_get_all_api() -> list[TrashBinVO]:
    return await get_trash_list()


@manage_api.post('/trash/edit', response_model=None)
async def trash_edit_api(trash_bin: TrashBinRO):
    await update_trash(trash_bin)


@manage_api.get('/database', response_model=None)
async def database_api(action: DatabaseActionEnum, background_task: BackgroundTasks):
    match action:
        case DatabaseActionEnum.RESTORE:
            background_task.add_task(database_restore)
        case DatabaseActionEnum.BACKUP:
            background_task.add_task(database_backup)
        case DatabaseActionEnum.DOWNLOAD:
            return FileResponse(DatabaseConfig.database, filename=DatabaseConfig.database)
    return None


@manage_api.post('/config/set', response_model=None)
async def config_set_api(config: ConfigRO):
    if config.value is None:
        await delete_config([config.key])
        return
    await set_config(config.key, config.value)


@manage_api.get('/config/get', response_model=str | None)
async def config_get_api(key: str) -> str | None:
    if key == ConfigKeyEnum.TOTP_SECRET:
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=HttpErrorDetail.CONFIG_NOT_ALLOWED)
    return await get_config(ConfigKeyEnum(key))


@manage_api.post('/user', response_model=None)
async def user_config_api(user: UserRO, request: Request):
    session_id = request.cookies.get(CommonConstant.SESSION_ID)
    await update_user_config(user, session_id)


@manage_api.get('/totp/enforce', response_model=str | None)
async def enforce_totp_secret_api(enforce: bool) -> str | None:
    return await enforce_totp(enforce)


@manage_api.get('/totp/confirm')
async def totp_enforce_confirm_api(totp: str):
    await confirm_totp(totp)
