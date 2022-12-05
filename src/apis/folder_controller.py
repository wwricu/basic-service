from fastapi import APIRouter, Response, Depends
from sqlalchemy.orm import Session

from models import Folder
from schemas import FolderInput, FolderOutput, UserOutput
from service import ResourceService
from core.dependency import get_db, RequiresRoles, requires_login


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


@folder_router.get("{url:path}", response_model=list[FolderOutput])
async def get_folder(url: str = None,
                     cur_user: UserOutput = Depends(requires_login),
                     db: Session = Depends(get_db)):
    folders = ResourceService.find_resources(Folder(url=url), db)
    assert len(folders) == 1
    ResourceService.check_permission(folders[0], cur_user, 1)
    sub_folders = ResourceService.find_resources(Folder(parent_id=folders[0].id), db)
    return [FolderOutput.init(x) for x in sub_folders]


@folder_router.put("",
                   dependencies=[Depends(RequiresRoles('admin'))],
                   response_model=FolderOutput)
async def modify_folder(folder: FolderInput,
                        db: Session = Depends(get_db)):
    return FolderOutput.init(ResourceService
                             .modify_resource(Folder.init(folder), db))


@folder_router.delete("/{folder_id}",
                      dependencies=[Depends(RequiresRoles('admin'))])
async def delete_folder(folder_id: int, db: Session = Depends(get_db)):
    ResourceService.remove_resource(Folder(id=folder_id), db)
    return Response(status_code=200)
