import asyncio
import pickle
from typing import cast, Coroutine

from anyio import Path
from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from config import Config
from dao import AsyncDatabase, AsyncRedis
from models import Content, Resource
from schemas import ContentInput, ContentOutput, UserOutput
from service import RoleRequired, ResourceService, SecurityService


content_router = APIRouter(
    prefix='/content',
    tags=['content'],
    dependencies=[Depends(AsyncDatabase.open_session)]
)


@content_router.post('', response_model=int)
async def add_content(
    content_input: ContentInput,
    cur_user: UserOutput = Depends(RoleRequired('admin')),
    redis: Redis = Depends(AsyncRedis.get_connection)
):
    content = Content(**content_input.dict())
    content.owner_id = cur_user.id
    content.permission = 700  # owner all, group 0, public 0
    content.parent_url = '/draft'

    content = await ResourceService.add_resource(content)
    for task in cast(list[Coroutine], (
        redis.set(f'content:id:{content.id}', pickle.dumps(content)),
        redis.set('count_dict', pickle.dumps(dict())),
        redis.set('preview_dict', pickle.dumps(dict()))
    )):
        asyncio.create_task(task)

    content_folder = Path(f'{Config.static.content_path}/{content.id}')
    if not await Path.exists(content_folder):
        asyncio.create_task(Path.mkdir(content_folder))
    return content.id


@content_router.get('/{content_id}', response_model=ContentOutput)
async def get_content(
    content_id: int,
    cur_user: UserOutput = Depends(SecurityService.optional_login_required),
    redis: Redis = Depends(AsyncRedis.get_connection)
):
    contents_str = await redis.get(f'content:id:{content_id}')
    if contents_str is not None:
        contents = [pickle.loads(contents_str)]
    else:
        contents = await ResourceService.find_resources(Content(id=content_id))
        asyncio.create_task(
            cast(Coroutine, redis.set(f'content:id:{content_id}',
                                      pickle.dumps(contents[0])))
        )
    assert len(contents) == 1
    ResourceService.check_permission(contents[0], cur_user, 1)
    return ContentOutput.init(contents[0])


@content_router.put(
    '', response_model=ContentOutput,
    dependencies=[Depends(RoleRequired('admin'))]
)
async def modify_content(
    content_input: ContentInput,
    redis: Redis = Depends(AsyncRedis.get_connection)
):
    await ResourceService.reset_content_tags(Content(**content_input.dict()))
    content = await ResourceService.modify_resource(
        Content(**content_input.dict())
    )
    for task in [
        ResourceService.trim_files(content_input.id, content_input.files),
        redis.set(f'content:id:{content.id}', pickle.dumps(content)),
        redis.set('count_dict', pickle.dumps(dict())),
        redis.set('preview_dict', pickle.dumps(dict()))
    ]:
        asyncio.create_task(task)

    return ContentOutput.init(content)


@content_router.delete(
    '/{content_id}', response_model=int,
    dependencies=[Depends(RoleRequired('admin'))]
)
async def delete_content(
    content_id: int,
    redis: Redis = Depends(AsyncRedis.get_connection)
):
    for task in [
        ResourceService.trim_files(content_id, set()),
        redis.delete(f'content:id:{content_id}'),
        redis.set('count_dict', pickle.dumps(dict())),
        redis.set('preview_dict', pickle.dumps(dict()))
    ]:
        asyncio.create_task(task)
    return await ResourceService.remove_resource(Resource(id=content_id))
