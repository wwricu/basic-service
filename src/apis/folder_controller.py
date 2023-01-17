from fastapi import APIRouter, Depends

from models import Folder, Content, Resource
from schemas import FolderInput, FolderOutput, UserOutput, ResourcePreview, ResourceQuery
from service import ResourceService, DatabaseService
from .auth_controller import RequiresRoles, optional_login_required


folder_router = APIRouter(prefix="/folder",
                          tags=["folder"],
                          dependencies=[Depends(DatabaseService.open_session)])


@folder_router.post("",
                    response_model=FolderOutput)
async def add_folder(folder_input: FolderInput,
                     cur_user: UserOutput = Depends(RequiresRoles('admin'))):
    folder = Folder(**folder_input.dict())
    folder.owner_id = cur_user.id
    folder.permission = 701  # owner all, group 0, public read
    return FolderOutput.init(ResourceService.add_resource(folder))


@folder_router.get("/count/{url:path}",
                   response_model=int)
async def get_sub_count(url: str = None,
                        resource_query: ResourceQuery = Depends(),
                        cur_user: UserOutput = Depends(optional_login_required)):
    if len(url) > 0 and url[0] != '/':
        url = f'/{url}'
    folders = ResourceService.find_resources(Folder(url=url))
    assert len(folders) == 1
    ResourceService.check_permission(folders[0], cur_user, 1)
    return ResourceService.find_sub_count(folders[0].url,
                                          resource_query,
                                          Content)


@folder_router.get("/sub_content/{url:path}",
                   response_model=list[ResourcePreview])
async def get_folder(url: str = '',
                     resource_query: ResourceQuery = Depends(),
                     cur_user: UserOutput = Depends(optional_login_required)):
    if len(url) > 0 and url[0] != '/':
        url = f'/{url}'
    folders = ResourceService.find_resources(Folder(url=url))
    assert len(folders) == 1
    ResourceService.check_permission(folders[0], cur_user, 1)
    sub_resources = ResourceService.find_sub_resources(url,
                                                       resource_query,
                                                       Content)
    return [ResourcePreview.init(x) for x in sub_resources]


@folder_router.put("",
                   dependencies=[Depends(RequiresRoles('admin'))],
                   response_model=FolderOutput)
async def modify_folder(folder_input: FolderInput):
    return FolderOutput.init(
        ResourceService.modify_resource(
            Folder(**folder_input.dict())
        ))


@folder_router.delete("/{folder_id}",
                      dependencies=[Depends(RequiresRoles('admin'))],
                      response_model=int)
async def delete_folder(folder_id: int = 0):
    return ResourceService.remove_resource(Resource(id=folder_id))
