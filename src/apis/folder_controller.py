from fastapi import APIRouter, Response, Depends
from sqlalchemy.orm import Session

from models import Folder
from schemas import FolderInput, FolderOutput
from service import ResourceService
from core.dependency import get_db, RequiresRoles


folder_router = APIRouter(prefix="/folder", tags=["folder"])


@folder_router.post("",
                    dependencies=[Depends(RequiresRoles('admin'))],
                    response_model=FolderOutput)
async def add_folder(folder: FolderInput,
                     db: Session = Depends(get_db)):
    return FolderOutput.init(ResourceService
                             .add_resource(Folder.init(folder), db))


@folder_router.get("", response_model=list[FolderOutput])
async def get_folder(folder_id: int = None,
                     url: str = None,
                     parent_id: int = None,
                     db: Session = Depends(get_db)):
    folders = ResourceService.find_resources(Folder(id=folder_id,
                                                    url=url,
                                                    parent_id=parent_id),
                                             db)
    return [FolderOutput.init(x) for x in folders]


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
