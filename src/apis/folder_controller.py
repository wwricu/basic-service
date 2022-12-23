from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models import Folder, Content, Resource
from schemas import FolderInput, FolderOutput, UserOutput, ResourcePreview
from service import ResourceService
from core.dependency import get_db, RequiresRoles, requires_login, optional_login_required


folder_router = APIRouter(prefix="/folder", tags=["folder"])


@folder_router.post("", response_model=FolderOutput)
async def add_folder(folder_input: FolderInput,
                     cur_user: UserOutput = Depends(RequiresRoles('admin')),
                     db: Session = Depends(get_db)):
    folder = Folder.init(folder_input)
    folder.owner_id = cur_user.id
    folder.permission = 701  # owner all, group 0, public read
    return FolderOutput.init(ResourceService
                             .add_resource(folder, db))

@folder_router.get("/count/{url:path}", response_model=int)
async def get_sub_count(url: str = None,
                        tag_id: int = 0,
                        cur_user: UserOutput = Depends(requires_login),
                        db: Session = Depends(get_db)):
    folders = ResourceService.find_resources(Folder(url=url), db)
    assert len(folders) == 1
    ResourceService.check_permission(folders[0], cur_user, 1)
    return ResourceService.find_sub_count(db, Content, folders[0].url, tag_id)


@folder_router.get("/sub_resources/{url:path}", response_model=list[ResourcePreview])
async def get_folder(url: str = '',
                     tag_id: int = 0,
                     page_idx: int = 0,
                     page_size: int = 0,
                     cur_user: UserOutput = Depends(optional_login_required),
                     db: Session = Depends(get_db)):
    folders = ResourceService.find_resources(Folder(url=url), db)
    assert len(folders) == 1
    ResourceService.check_permission(folders[0], cur_user, 1)
    sub_resources = ResourceService.find_sub_resources(db,
                                                       Resource,
                                                       url,
                                                       tag_id,
                                                       page_idx,
                                                       page_size)
    return [ResourcePreview.init(x) for x in sub_resources]


@folder_router.put("",
                   dependencies=[Depends(RequiresRoles('admin'))],
                   response_model=FolderOutput)
async def modify_folder(folder: FolderInput,
                        db: Session = Depends(get_db)):
    return FolderOutput.init(ResourceService
                             .modify_resource(Folder.init(folder), db))


@folder_router.delete("/{folder_id}",
                      dependencies=[Depends(RequiresRoles('admin'))])
async def delete_folder(folder_id: int = 0, db: Session = Depends(get_db)):
    return ResourceService.remove_resource(Resource(id=folder_id), db)
