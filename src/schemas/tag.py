from pydantic import BaseModel
from models import Folder, Content, Tag


class TagSchema(BaseModel):
    id: int = None,
    name: str = None


class ContentTags(BaseModel):
    content_id: int = None
    remove_tag_ids: list[int] = None
    add_tag_ids: list[int] = None
    current_tags: list[Tag] = None


class TagContents(BaseModel):
    tag_id: int = None
    remove_content_ids: list[int] = None
    add_content_ids: list[int] = None
    current_contents: list[Tag] = None
