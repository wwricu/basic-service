import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Body, Depends
from fastapi.responses import FileResponse

from wwricu.component import database as database_manager
from wwricu.component.cache import query_cache
from wwricu.config import app_config
from wwricu.domain.common import TrashBinRO, TrashBinVO
from wwricu.domain.enum import ConfigKeyEnum, DatabaseActionEnum, EntityTypeEnum, ManageCommandEnum
from wwricu.service import common_service, manage_service, post_service, security_service, tag_service

manage_api = APIRouter(prefix='/admin/manage', dependencies=[Depends(security_service.require_admin)])


@manage_api.get('/trash/all', response_model=list[TrashBinVO])
async def trash_get_all_api() -> list[TrashBinVO]:
    return await manage_service.list_trash()


@manage_api.post('/trash/edit', dependencies=[Depends(common_service.reset_sys_config)], response_model=None)
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
async def database_download_api(background_task: BackgroundTasks):
    await database_manager.backup(snapshot := uuid.uuid4().hex)
    background_task.add_task(Path(snapshot).unlink, missing_ok=True)
    return FileResponse(snapshot, filename=app_config.database.name)


@manage_api.post('/database', response_model=None)
async def database_api(background_task: BackgroundTasks, action: DatabaseActionEnum = Body(embed=True)):
    match action:
        case DatabaseActionEnum.RESTORE:
            background_task.add_task(common_service.restore_database)
        case DatabaseActionEnum.BACKUP:
            background_task.add_task(common_service.backup_database)


@manage_api.post('/command', response_model=str | None)
async def command_api(command: ManageCommandEnum = Body(embed=True), value: str = Body(embed=True)) -> str | None:
    return await manage_service.write(command, value)


@manage_api.get('/config/get', response_model=str | None)
async def config_get_api(key: ConfigKeyEnum) -> str | None:
    return await manage_service.read(key)
