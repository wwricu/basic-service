from anyio import Path
from fastapi import APIRouter, Depends

from dao import AsyncDatabase
from models import Content, Resource
from schemas import ContentInput, ContentOutput, UserOutput
from service import RequiresRoles, ResourceService, SecurityService


content_router = APIRouter(
    prefix="/content",
    tags=["content"],
    dependencies=[Depends(AsyncDatabase.open_session)]
)


@content_router.post("", response_model=int)
async def add_content(
        content_input: ContentInput,
        cur_user: UserOutput = Depends(RequiresRoles('admin'))
):

    content = Content(**content_input.dict())
    content.owner_id = cur_user.id
    content.permission = 700  # owner all, group 0, public 0
    content.parent_url = '/draft'
    id = (await ResourceService.add_resource(content)).id
    content_folder = Path(f'static/content/{id}')
    if not await Path.exists(content_folder):
        await Path.mkdir(content_folder)
    return id


@content_router.get("/{content_id}", response_model=ContentOutput)
async def get_content(
        content_id: int,
        cur_user: UserOutput = Depends(SecurityService.optional_login_required)
):
    contents = await ResourceService.find_resources(Content(id=content_id))
    assert len(contents) == 1
    ResourceService.check_permission(contents[0], cur_user, 1)
    return ContentOutput.init(contents[0])


@content_router.put(
    "", response_model=ContentOutput,
    dependencies=[Depends(RequiresRoles('admin'))]
)
async def modify_content(content: ContentInput):
    await ResourceService.trim_files(content.id, content.files)
    await ResourceService.reset_content_tags(Content(**content.dict()))
    content = await ResourceService.modify_resource(Content(**content.dict()))
    return ContentOutput.init(content)


@content_router.delete(
    "/{content_id}", response_model=int,
    dependencies=[Depends(RequiresRoles('admin'))]
)
async def delete_content(content_id: int):
    await ResourceService.trim_files(content_id, set())
    return await ResourceService.remove_resource(Resource(id=content_id))
