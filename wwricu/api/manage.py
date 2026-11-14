from fastapi import APIRouter, Body, Depends

from wwricu.component.cache import query_cache
from wwricu.domain.common import TrashBinRO, TrashBinVO
from wwricu.domain.enum import ConfigKeyEnum, EntityTypeEnum, ManageCommandEnum
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


@manage_api.post('/command', response_model=str | None)
async def command_api(command: ManageCommandEnum = Body(embed=True), value: str = Body(embed=True)) -> str | None:
    return await manage_service.write(command, value)


@manage_api.get('/config/get', response_model=str | None)
async def config_get_api(key: ConfigKeyEnum) -> str | None:
    return await manage_service.read(key)
