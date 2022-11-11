from pydantic import BaseModel
from datetime import datetime


class ResourceSchema(BaseModel):
    id: int = None
    title: str = None
    url: str = None
    created_time: datetime = None
    modified_time: datetime = None
    parent_id: int = None

    class Config:
        orm_mode = True


class ContentSchema(ResourceSchema):
    sub_title: str = None
    status: str = None
    content: str = None

    class Config:
        orm_mode = True


class FolderSchema(ResourceSchema):

    class Config:
        orm_mode = True
