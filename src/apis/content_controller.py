import pickle

from anyio import Path
from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from dao import AsyncDatabase, AsyncRedis
from models import Content, Resource
from schemas import ContentInput, ContentOutput, UserOutput
from service import RoleRequired, ResourceService, SecurityService


content_router = APIRouter(
    prefix="/content",
    tags=["content"],
    dependencies=[Depends(AsyncDatabase.open_session)]
)


@content_router.post("", response_model=int)
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
    await redis.set(f'content:id:{content.id}', pickle.dumps(content))

    content_folder = Path(f'static/content/{content.id}')
    if not await Path.exists(content_folder):
        await Path.mkdir(content_folder)
    return content.id


@content_router.get("/{content_id}", response_model=ContentOutput)
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
        await redis.set(f'content:id:{content_id}', pickle.dumps(contents[0]))
    assert len(contents) == 1
    ResourceService.check_permission(contents[0], cur_user, 1)
    return ContentOutput.init(contents[0])


@content_router.put(
    "", response_model=ContentOutput,
    dependencies=[Depends(RoleRequired('admin'))]
)
async def modify_content(
    content: ContentInput,
    redis: Redis = Depends(AsyncRedis.get_connection)
):
    await ResourceService.trim_files(content.id, content.files)
    await ResourceService.reset_content_tags(Content(**content.dict()))
    content = await ResourceService.modify_resource(Content(**content.dict()))
    await redis.set(f'content:id:{content.id}', pickle.dumps(content))
    return ContentOutput.init(content)


@content_router.delete(
    "/{content_id}", response_model=int,
    dependencies=[Depends(RoleRequired('admin'))]
)
async def delete_content(
    content_id: int,
    redis: Redis = Depends(AsyncRedis.get_connection)
):
    await ResourceService.trim_files(content_id, set())
    await redis.delete(f'content:id:{content_id}')
    return await ResourceService.remove_resource(Resource(id=content_id))
