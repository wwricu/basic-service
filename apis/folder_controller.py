from models import Folder
from fastapi import Depends, APIRouter

from dao import BaseDao
from models import Folder
from schemas import FolderInput
from service import ResourceService


content_router = APIRouter(prefix="/folder")


@content_router.post("")
async def add_folder(folder: FolderInput):
    return ResourceService.add_resource(Folder(title=folder.title,
                                               parent_id=folder.parent_id))


@content_router.put("")
async def modify_folder(folder: FolderInput):
    return ResourceService.modify_resource(Folder(id=folder.id,
                                                  title=folder.title,
                                                  parent_id=folder.parent_id))


@content_router.delete("/{folder_id}")
async def delete_folder(folder_id: int):
    return ResourceService.remove_resource(Folder(id=folder_id))
