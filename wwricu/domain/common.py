import time
from datetime import datetime

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field

from wwricu.domain.enum import EntityTypeEnum


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRO(BaseModel):
    username: str = ''
    password: str = ''
    totp: str | None = None


class PageVO[T](BaseModel):
    page_index: int
    page_size: int
    count: int
    data: list[T] = Field(default_factory=list)


class FileUploadVO(BaseModel):
    id: int
    name: str | None = None
    key: str
    location: str


class SiteVO(BaseModel):
    title: str
    tagline: str
    content: str
    post_count: int
    category_count: int
    tag_count: int


class TrashBinRO(BaseModel):
    id: int
    type: EntityTypeEnum
    delete: bool | None = False


class TrashBinVO(BaseModel):
    id: int
    name: str
    info: str | None = None
    type: EntityTypeEnum
    delete_time: datetime


class LoginVO(BaseModel):
    detail: str | None = None


class SessionVO(BaseModel):
    id: str
    ua: str = ''
    last_active: datetime = Field(default_factory=datetime.now)
    issue_time: int = Field(default_factory=lambda: int(time.time()))
