from models import Folder
from fastapi import Depends, APIRouter

from dao import BaseDao
from schemas import FolderSchema
from models import Folder


content_router = APIRouter(prefix="/folder")


@content_router.post("")
async def add_folder(folder: FolderSchema):
    print(folder.title)
    new_folder = Folder(title=folder.title,
                        url=folder.url,
                        parent_id=folder.parent_id)
    return BaseDao.insert(new_folder)


@content_router.put("")
async def modify_folder(folder: FolderSchema):
    return BaseDao.update(Folder(title=folder.title,
                                 url=folder.url,
                                 parent_id=folder.parent_id), Folder)


@content_router.delete("/{folder_id}")
async def modify_folder(folder_id: int):
    return BaseDao.delete(Folder(id=folder_id), Folder)
