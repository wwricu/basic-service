from datetime import datetime

from pydantic import Field

from wwricu.domain.common import BaseModel
from wwricu.domain.enum import PostResourceTypeEnum, PostStatusEnum
from wwricu.domain.tag import TagVO


class PostRequestRO(BaseModel):
    page_index: int = 1
    page_size: int = 10
    tag_list: list[str] | None = None
    category: str | None = None
    status: PostStatusEnum | None = None
    deleted: bool = None


class PostUpdateRO(BaseModel):
    """All not null fields are mandatory"""
    id: int
    title: str
    cover_id: int | None = None
    preview: str
    status: PostStatusEnum
    content: str
    tag_id_list: list[int]
    category_id: int | None = None


class PostResourceVO(BaseModel):
    id: int
    name: str | None = None
    key: str
    url: str
    type: PostResourceTypeEnum


class PostDetailVO(BaseModel):
    id: int
    title: str | None = None
    cover: PostResourceVO | None = None
    preview: str = ''
    content: str = ''
    tag_list: list[TagVO] = Field(default_factory=list)
    category: TagVO | None = None
    status: PostStatusEnum | None = None
    create_time: datetime | None = None
    update_time: datetime | None = None
