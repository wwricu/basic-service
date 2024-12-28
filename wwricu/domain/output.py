from __future__ import annotations

from dataclasses import field
from datetime import datetime

from wwricu.domain.common import BaseModel
from wwricu.domain.entity import BlogPost, PostTag
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


class PostPreviewVO(BaseModel):
    id: int
    title: str
    preview: str = ''
    tags: list[TagVO] = field(default_factory=list)
    category: TagVO | None = None
    status: PostStatusEnum
    create_time: datetime | None = None
    update_time: datetime | None = None

    @classmethod
    def of(cls, post: BlogPost, category: PostTag | None = None, tag_list: list[PostTag] | None = ()) -> PostPreviewVO:
        preview = cls(
            id=post.id,
            title=post.title,
            status=PostStatusEnum(post.status),
            create_time=post.create_time,
            update_time=post.update_time
        )
        if post.content is not None:
            preview.preview = post.content[30:]
        preview.category = TagVO.of(category)
        preview.tags = [TagVO.of(tag) for tag in tag_list]
        return preview


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
    content: str = ''
    tag_list: list[TagVO] = field(default_factory=list)
    category: TagVO | None = None
    status: PostStatusEnum | None = None
    create_time: datetime | None = None
    update_time: datetime | None = None

    @classmethod
    def of(cls, post: BlogPost, category: PostTag | None = None, tag_list: list[PostTag] | None = ()) -> PostDetailVO:
        post_detail = cls(
            id=post.id,
            title=post.title,
            content=post.content,
            status=PostStatusEnum(post.status),
            create_time=post.create_time,
            update_time=post.update_time
        )
        post_detail.category = TagVO.of(category)
        post_detail.tag_list = [TagVO.of(tag) for tag in tag_list]
        return post_detail


class FileUploadVO(BaseModel):
    name: str
    key: str
    location: str
