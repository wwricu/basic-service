from pydantic import BaseModel
from datetime import datetime


class ResourceBase(BaseModel):
    id: int = None
    title: str = None
    parent_id: int = None


class ContentInput(ResourceBase):
    sub_title: str = None
    status: str = None
    content: str = None


class FolderInput(ResourceBase):
    pass


class ResourceOutput(ResourceBase):
    url: str = None
    created_time: datetime = None
    modified_time: datetime = None


class ContentOutput(ResourceOutput):
    sub_title: str = None
    status: str = None
    content: str = None


class FolderOutput(ResourceBase):
    pass
