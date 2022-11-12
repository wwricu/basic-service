from fastapi import APIRouter

from models import Folder
from schemas import FolderInput, FolderOutput
from service import ResourceService


content_router = APIRouter(prefix="/folder")


@content_router.post("", response_model=FolderOutput)
async def add_folder(folder: FolderInput):
    return ResourceService.add_resource(Folder(title=folder.title,
                                               parent_id=folder.parent_id))


@content_router.get("",  response_model=list[FolderOutput])
async def get_folder(folder_id: int = None,
                     url: str = None,
                     parent_id: int = None):
    return ResourceService.find_resources(Folder(id=folder_id,
                                                 url=url,
                                                 parent_id=parent_id))


@content_router.put("", response_model=FolderOutput)
async def modify_folder(folder: FolderInput):
    return ResourceService.modify_resource(Folder(id=folder.id,
                                                  title=folder.title,
                                                  parent_id=folder.parent_id))


@content_router.delete("/{folder_id}", response_model=int)
async def delete_folder(folder_id: int):
    return ResourceService.remove_resource(Folder(id=folder_id))
