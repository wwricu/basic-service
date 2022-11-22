from pydantic import BaseModel
from datetime import datetime
from models import Folder, Content
from .tag import TagSchema


class ResourceBase(BaseModel):
    id: int = None
    title: str = None
    parent_id: int = None


class FolderInput(ResourceBase):
    pass


class ContentInput(FolderInput):
    sub_title: str = None
    status: str = None
    content: bytes = None


class FolderOutput(ResourceBase):
    @classmethod
    def init(cls, folder: Folder):
        if not isinstance(folder, Folder):
            return None
        return FolderOutput(id=folder.id,
                            url=folder.url,
                            title=folder.title,
                            parent_id=folder.parent_id,
                            created_time=folder.created_time,
                            modified_time=folder.updated_time)

    url: str = None
    created_time: datetime = None
    updated_time: datetime = None


class ContentPreview(FolderOutput):
    @classmethod
    def init(cls, content: Content):
        if not isinstance(content, Content):
            return None
        return ContentOutput(id=content.id,
                             title=content.title,
                             url=content.url,
                             parent_id=content.parent_id,
                             created_time=content.created_time,
                             updated_time=content.updated_time,
                             parent=FolderOutput.init(content.parent),
                             author_id=content.author_id,
                             sub_title=content.sub_title,
                             status=content.status,
                             tags=[TagSchema(id=x.id,
                                             name=x.name)
                                   for x in content.tags])

    parent: FolderOutput = None
    author_id: int = None
    sub_title: str = None
    status: str = None
    tags: list[TagSchema] = None


class ContentOutput(ContentPreview):
    @classmethod
    def init(cls, content: Content):
        if not isinstance(content, Content):
            return None
        return ContentOutput(id=content.id,
                             title=content.title,
                             url=content.url,
                             parent_id=content.parent_id,
                             created_time=content.created_time,
                             updated_time=content.updated_time,
                             author_id=content.author_id,
                             sub_title=content.sub_title,
                             status=content.status,
                             tags=[TagSchema(id=x.id,
                                             name=x.name)
                                   for x in content.tags],
                             content=content.content)

    content: bytes = None
