import os
from fastapi import APIRouter, Depends, HTTPException

from dao import AsyncDatabase
from models import Content, Resource
from schemas import ContentInput, ContentOutput, UserOutput
from service import ResourceService
from .auth_controller import RequiresRoles, optional_login_required


content_router = APIRouter(prefix="/content",
                           tags=["content"],
                           dependencies=[Depends(AsyncDatabase.open_session)])


@content_router.post("", response_model=int)
async def add_content(content_input: ContentInput,
                      cur_user: UserOutput = Depends(RequiresRoles('admin'))):
    content = Content(**content_input.dict())
    content.owner_id = cur_user.id
    content.permission = 700  # owner all, group 0, public 0
    content.parent_url = '/draft'
    id = (await ResourceService.add_resource(content)).id
    content_folder = f'static/content/{id}'
    if not os.path.exists(content_folder):
        os.makedirs(content_folder)
    return id


@content_router.get("/{content_id}", response_model=ContentOutput)
async def get_content(content_id: int,
                      cur_user: UserOutput = Depends(optional_login_required)):
    contents = await ResourceService.find_resources(Content(id=content_id))
    if len(contents) != 1 or not ResourceService.check_permission(
            contents[0], cur_user, 1):
        raise HTTPException(status_code=403, detail="need login to check draft")
    return ContentOutput.init(contents[0])


@content_router.put("",
                    dependencies=[Depends(RequiresRoles('admin'))],
                    response_model=ContentOutput)
async def modify_content(content: ContentInput):
    await ResourceService.trim_files(content.id, content.files)
    await ResourceService.reset_content_tags(Content(**content.dict()))
    content = await ResourceService.modify_resource(Content(**content.dict()))
    return ContentOutput.init(content)


@content_router.delete("/{content_id}",
                       dependencies=[Depends(RequiresRoles('admin'))])
async def delete_content(content_id: int):
    await ResourceService.trim_files(content_id, set())
    return await ResourceService.remove_resource(Resource(id=content_id))
