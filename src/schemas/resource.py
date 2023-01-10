from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime
from models import Resource, Folder, Content
from .tag import TagSchema


class ResourceBase(BaseModel):
    id: int = None
    title: str = None
    parent_url: str = None
    permission: int = None


class FolderInput(ResourceBase):
    pass


class ContentInput(FolderInput):
    category: TagSchema = None
    tags: list[TagSchema] = []
    sub_title: str = None
    files: set = None
    content: bytes = None


class FolderOutput(ResourceBase):
    @classmethod
    def init(cls, folder: Folder) -> FolderOutput | None:
        if not isinstance(folder, Folder):
            return None
        return FolderOutput(id=folder.id,
                            url=folder.url,
                            title=folder.title,
                            parent_url=folder.parent_url,
                            created_time=folder.created_time,
                            updated_time=folder.updated_time)

    url: str = None
    created_time: datetime = None
    updated_time: datetime = None


class ResourcePreview(FolderOutput):
    @classmethod
    def init(cls, resource: Resource) -> ResourcePreview | None:
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
                                     for x in resource.tags]
                               if hasattr(resource, 'tags') else None,
                               category=TagSchema(id=resource.category.id,
                                                  name=resource.category.name)
                               if hasattr(resource, 'category') and resource.category is not None
                               else None)

    owner_id: int = None
    type: str = None
    tags: list[TagSchema] = None
    category: TagSchema = None


class ContentOutput(ResourcePreview):
    @classmethod
    def init(cls, content: Content) -> ContentOutput | None:
        if not isinstance(content, Content):
            return None
        return ContentOutput(id=content.id,
                             title=content.title,
                             url=content.url,
                             parent_url=content.parent_url,
                             created_time=content.created_time,
                             updated_time=content.updated_time,
                             owner_id=content.owner_id,
                             sub_title=content.sub_title,
                             tags=[TagSchema(id=x.id,
                                             name=x.name)
                                   for x in content.tags],
                             category=TagSchema(id=content.category.id,
                                                name=content.category.name)
                             if content.category is not None else None,
                             content=content.content)

    content: bytes = None
