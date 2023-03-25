import asyncio
import pickle

from fastapi import APIRouter, Depends

from dao import AsyncDatabase, AsyncRedis, RedisKey
from models import Content, Folder, Resource
from schemas import (
    FolderInput,
    FolderOutput,
    ResourcePreview,
    ResourceQuery,
    UserOutput
)
from service import RoleRequired, ResourceService, SecurityService


folder_router = APIRouter(
    prefix='/folder',
    tags=['folder'],
    dependencies=[Depends(AsyncDatabase.open_session)]
)


@folder_router.post('', response_model=FolderOutput)
async def add_folder(
    folder_input: FolderInput,
    cur_user: UserOutput = Depends(RoleRequired('admin'))
):

    folder = Folder(**folder_input.dict())
    folder.owner_id = cur_user.id
    folder.permission = 701  # owner all, group 0, public read
    return FolderOutput.init(
        await ResourceService.add_resource(folder)
    )


@folder_router.get('/count/{url:path}', response_model=int)
async def get_sub_count(
    url: str = None,
    resource_query: ResourceQuery = Depends(),
    cur_user: UserOutput = Depends(SecurityService.optional_login_required),
    redis: AsyncRedis = Depends(AsyncRedis.get_connection)
):
    if len(url) > 0 and url[0] != '/':
        url = f'/{url}'

    folders_str = await redis.get(RedisKey.folder(url))
    if folders_str is not None:
        folders = pickle.loads(folders_str)
    else:
        folders = await ResourceService.find_resources(Folder(url=url))
        asyncio.create_task(redis.set(
            RedisKey.folder(url), pickle.dumps(folders)
        ))

    assert len(folders) == 1
    ResourceService.check_permission(folders[0], cur_user, 1)

    field = RedisKey.count_field(
        url,
        resource_query.category_name,
        resource_query.tag_name
    )
    count_str = await redis.hget(RedisKey.COUNT_DICT, field)
    if count_str is not None:
        return int(count_str.decode())
    count = await ResourceService.find_sub_count(
        folders[0].url,
        resource_query,
        Content
    )
    asyncio.create_task(redis.hset(RedisKey.COUNT_DICT, field, str(count)))
    return count


@folder_router.get(
    '/sub_content/{url:path}',
    response_model=list[ResourcePreview]
)
async def get_folder(
    url: str = '',
    resource_query: ResourceQuery = Depends(),
    cur_user: UserOutput = Depends(SecurityService.optional_login_required),
    redis: AsyncRedis = Depends(AsyncRedis.get_connection)
):
    if len(url) > 0 and url[0] != '/':
        url = f'/{url}'

    folders_str = await redis.get(RedisKey.folder(url))
    if folders_str is not None:
        folders = pickle.loads(folders_str)
    else:
        folders = await ResourceService.find_resources(Folder(url=url))
        asyncio.create_task(redis.set(
            RedisKey.folder(url), pickle.dumps(folders)
        ))

    assert len(folders) == 1
    ResourceService.check_permission(folders[0], cur_user, 1)

    field = RedisKey.preview_field(
        url,
        resource_query.category_name,
        resource_query.tag_name,
        resource_query.page_idx,
        resource_query.page_size
    )
    resource_str = await redis.hget(RedisKey.PREVIEW_DICT, field)
    if resource_str is not None:
        return [ResourcePreview.init(x) for x in pickle.loads(resource_str)]

    sub_resources = await ResourceService.find_sub_resources(
        url, resource_query, Content
    )
    asyncio.create_task(redis.hset(
        RedisKey.PREVIEW_DICT, field, pickle.dumps(sub_resources)
    ))
    return [ResourcePreview.init(x) for x in sub_resources]


@folder_router.put(
    '', response_model=FolderOutput,
    dependencies=[Depends(RoleRequired('admin'))]
)
async def modify_folder(folder_input: FolderInput):
    return FolderOutput.init(
        await ResourceService.modify_resource(
            Folder(**folder_input.dict())
        )
    )


@folder_router.delete(
    '/{folder_id}', response_model=int,
    dependencies=[Depends(RoleRequired('admin'))]
)
async def delete_folder(folder_id: int = 0):
    return await ResourceService.remove_resource(Resource(id=folder_id))
