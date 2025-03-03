from __future__ import annotations

from dataclasses import field
from datetime import datetime

from wwricu.domain.common import BaseModel
from wwricu.domain.enum import PostResourceTypeEnum, PostStatusEnum, TagTypeEnum


class TagVO(BaseModel):
    id: int
    name: str
    type: TagTypeEnum
    count: int | None = None


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
    tag_list: list[TagVO] = field(default_factory=list)
    category: TagVO | None = None
    status: PostStatusEnum | None = None
    create_time: datetime | None = None
    update_time: datetime | None = None


class PageVO[T](BaseModel):
    page_index: int
    page_size: int
    count: int
    post_details: list[T] = field(default_factory=list)


class FileUploadVO(BaseModel):
    id: int
    name: str
    key: str
    location: str


class AboutPageVO(BaseModel):
    content: str = ''
    post_count: int = 0
    category_count: int = 0
    tag_count: int = 0
