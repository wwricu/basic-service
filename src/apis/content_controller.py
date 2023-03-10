import asyncio
import pickle

from fastapi import APIRouter, Depends

from dao import AsyncDatabase, AsyncRedis
from models import Content, Resource
from schemas import AlgoliaPostIndex, ContentInput, ContentOutput, UserOutput
from service import (
    AlgoliaService,
    RoleRequired,
    ResourceService,
    SecurityService
)


content_router = APIRouter(
    prefix='/content',
    tags=['content'],
    dependencies=[Depends(AsyncDatabase.open_session)]
)


@content_router.post('', response_model=int)
async def add_content(
    content_input: ContentInput,
    cur_user: UserOutput = Depends(RoleRequired('admin')),
    redis: AsyncRedis = Depends(AsyncRedis.get_connection)
):
    content = Content(**content_input.dict())
    content.owner_id = cur_user.id
    content.permission = 700  # owner all, group 0, public 0
    content.parent_url = '/draft'

    content = await ResourceService.add_resource(content)
    for task in (
        redis.set(f'content:id:{content.id}', pickle.dumps(content)),
        redis.delete('count_dict'),
        redis.delete('preview_dict')
    ):
        asyncio.create_task(task)

    return content.id


@content_router.get('/{content_id}', response_model=ContentOutput)
async def get_content(
    content_id: int,
    cur_user: UserOutput = Depends(SecurityService.optional_login_required),
    redis: AsyncRedis = Depends(AsyncRedis.get_connection)
):
    contents_str = await redis.get(f'content:id:{content_id}')
    if contents_str is not None:
        contents = [pickle.loads(contents_str)]
    else:
        contents = await ResourceService.find_resources(Content(id=content_id))
        asyncio.create_task(
            redis.set(f'content:id:{content_id}', pickle.dumps(contents[0]))
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
    redis: AsyncRedis = Depends(AsyncRedis.get_connection)
):
    await ResourceService.reset_content_tags(Content(**content_input.dict()))
    content = await ResourceService.modify_resource(
        Content(**content_input.dict())
    )
    for task in (
        AlgoliaService.save_contents(
            [AlgoliaPostIndex.parse_content(content)]
        ) if content.parent_url == '/post'  # algolia save/delete task
        else AlgoliaService.delete_contents([content.id]),
        ResourceService.trim_files(content_input.id, content_input.files),
        redis.set(f'content:id:{content.id}', pickle.dumps(content)),
        redis.delete('count_dict'),
        redis.delete('preview_dict')
    ):
        asyncio.create_task(task)

    return ContentOutput.init(content)


@content_router.delete(
    '/{content_id}', response_model=int,
    dependencies=[Depends(RoleRequired('admin'))]
)
async def delete_content(
    content_id: int,
    redis: AsyncRedis = Depends(AsyncRedis.get_connection)
):
    for task in (
        AlgoliaService.delete_contents([content_id]),
        ResourceService.trim_files(content_id, set()),
        redis.delete(f'content:id:{content_id}'),
        redis.delete('count_dict'),
        redis.delete('preview_dict')
    ):
        asyncio.create_task(task)
    return await ResourceService.remove_resource(Resource(id=content_id))
