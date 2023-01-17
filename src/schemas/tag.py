from __future__ import annotations
from pydantic import BaseModel
from models import Tag


class TagSchema(BaseModel):
    @classmethod
    def init(cls, tag: Tag) -> TagSchema | None:
        if tag is None:
            return None
        return TagSchema(id=tag.id, name=tag.name)

    id: int = None
    name: str = None


class ContentTags(BaseModel):
    content_id: int = None
    remove_tag_ids: list[int] = None
    add_tag_ids: list[int] = None
    current_tags: list[TagSchema] = None


class TagContents(BaseModel):
    tag_id: int = None
    remove_content_ids: list[int] = None
    add_content_ids: list[int] = None
    current_contents: list[TagSchema] = None
