from fastapi import APIRouter

from models import Folder
from schemas import FolderInput, FolderOutput
from service import ResourceService


folder_router = APIRouter(prefix="/folder")


@folder_router.post("", response_model=FolderOutput)
async def add_folder(folder: FolderInput):
    return FolderOutput.init(ResourceService
                             .add_resource(Folder(title=folder.title,
                                                  parent_id=folder.parent_id)))


@folder_router.get("",  response_model=list[FolderOutput])
async def get_folder(folder_id: int = None,
                     url: str = None,
                     parent_id: int = None):
    return FolderOutput.init(ResourceService
                             .find_resources(Folder(id=folder_id,
                                                    url=url,
                                                    parent_id=parent_id)))


@folder_router.put("", response_model=FolderOutput)
async def modify_folder(folder: FolderInput):
    return FolderOutput.init(ResourceService
                             .modify_resource(Folder(id=folder.id,
                                                     title=folder.title,
                                                     parent_id=folder.parent_id)))


@folder_router.delete("/{folder_id}", response_model=None)
async def delete_folder(folder_id: int):
    ResourceService.remove_resource(Folder(id=folder_id))
