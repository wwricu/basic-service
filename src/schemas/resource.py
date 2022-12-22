from pydantic import BaseModel
from datetime import datetime
from models import Resource, Folder, Content
from .tag import TagSchema


class ResourceBase(BaseModel):
    id: int = None
    title: str = None
    parent_url: str = None
    permission: int = 0


class FolderInput(ResourceBase):
    pass


class ContentInput(FolderInput):
    tags: list[TagSchema] = []
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
                            parent_url=folder.parent_url,
                            created_time=folder.created_time,
                            modified_time=folder.updated_time)

    url: str = None
    created_time: datetime = None
    updated_time: datetime = None


class ResourcePreview(FolderOutput):
    @classmethod
    def init(cls, resource: Resource):
        if resource is None:
            return None
        return ResourcePreview(id=resource.id,
                               title=resource.title,
                               url=resource.url,
                               parent_url=resource.parent_url,
                               created_time=resource.created_time,
                               updated_time=resource.updated_time,
                               owner_id=resource.owner_id,
                               type=resource.__class__.__name__,
                               tags=[TagSchema(id=x.id,
                                               name=x.name)
                                     for x in resource.tags])

    parent: FolderOutput = None
    owner_id: int = None
    status: str = None
    type: str = None
    tags: list[TagSchema] = None


class ContentOutput(ResourcePreview):
    @classmethod
    def init(cls, content: Content):
        if not isinstance(content, Content):
            return None
        return ContentOutput(id=content.id,
                             title=content.title,
                             url=content.url,
                             parent_url=content.parent_url,
                             parent=FolderOutput.init(content.parent),
                             created_time=content.created_time,
                             updated_time=content.updated_time,
                             owner_id=content.owner_id,
                             sub_title=content.sub_title,
                             status=content.status,
                             tags=[TagSchema(id=x.id,
                                             name=x.name)
                                   for x in content.tags],
                             content=content.content)

    content: bytes = None
