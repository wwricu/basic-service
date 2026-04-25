from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from wwricu.config import DatabaseConfig
from wwricu.component.database import database_restore, database_backup
from wwricu.domain.common import ConfigRO, TrashBinRO, TrashBinVO, UserRO
from wwricu.domain.constant import CommonConstant, HttpErrorDetail
from wwricu.domain.enum import ConfigKeyEnum, DatabaseActionEnum
from wwricu.service import manage_service, security_service

manage_api = APIRouter(prefix='/manage', tags=['Manage API'], dependencies=[Depends(security_service.require_admin)])


@manage_api.get('/trash/all', response_model=list[TrashBinVO])
async def trash_get_all_api() -> list[TrashBinVO]:
    return await manage_service.list_trash()


@manage_api.post('/trash/edit', response_model=None)
async def trash_edit_api(trash_bin: TrashBinRO):
    await manage_service.process_trash(trash_bin)


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
        await manage_service.delete_config([config.key])
        return
    await manage_service.set_config(config.key, config.value)


@manage_api.get('/config/get', response_model=str | None)
async def config_get_api(key: str) -> str | None:
    if key == ConfigKeyEnum.TOTP_SECRET:
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=HttpErrorDetail.CONFIG_NOT_ALLOWED)
    return await manage_service.get_config(ConfigKeyEnum(key))


@manage_api.post('/user', response_model=None)
async def user_config_api(user: UserRO, request: Request):
    session_id = request.cookies.get(CommonConstant.SESSION_ID)
    await manage_service.update_admin_user(user, session_id)


@manage_api.get('/totp/enforce', response_model=str | None)
async def enforce_totp_secret_api(enforce: bool) -> str | None:
    return await manage_service.enforce_totp(enforce)


@manage_api.get('/totp/confirm')
async def totp_enforce_confirm_api(totp: str):
    await manage_service.confirm_totp(totp)
