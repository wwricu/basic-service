from fastapi import APIRouter, Response

from models import Folder
from schemas import FolderInput, FolderOutput
from service import ResourceService


folder_router = APIRouter(prefix="/folder", tags=["folder"])


@folder_router.post("", response_model=FolderOutput)
async def add_folder(folder: FolderInput):
    return FolderOutput.init(ResourceService
                             .add_resource(Folder.init(folder)))


@folder_router.get("",  response_model=list[FolderOutput])
async def get_folder(folder_id: int = None,
                     url: str = None,
                     parent_id: int = None):
    folders = ResourceService.find_resources(Folder(id=folder_id,
                                                    url=url,
                                                    parent_id=parent_id))
    return [FolderOutput.init(x) for x in folders]


@folder_router.put("", response_model=FolderOutput)
async def modify_folder(folder: FolderInput):
    return FolderOutput.init(ResourceService
                             .modify_resource(Folder.init(folder)))


@folder_router.delete("/{folder_id}")
async def delete_folder(folder_id: int):
    ResourceService.remove_resource(Folder(id=folder_id))
    return Response(status_code=200)
