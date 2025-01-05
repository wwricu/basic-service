from __future__ import annotations

from dataclasses import field
from datetime import datetime

from wwricu.domain.common import BaseModel
from wwricu.domain.entity import PostTag
from wwricu.domain.enum import TagTypeEnum, PostResourceTypeEnum, PostStatusEnum


class TagVO(BaseModel):
    id: int
    name: str
    type: TagTypeEnum

    @classmethod
    def of(cls, tag: PostTag) -> TagVO | None:
        if tag is None:
            return None
        return cls(id=tag.id, name=tag.name, type=TagTypeEnum(tag.type))


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


class PostDetailPageVO(BaseModel):
    page_index: int
    page_size: int
    count: int
    post_details: list[PostDetailVO] = field(default_factory=list)


class FileUploadVO(BaseModel):
    id: int
    name: str
    key: str
    location: str
