from __future__ import annotations
import base64
from datetime import datetime

from pydantic import BaseModel

from models import Content


class AlgoliaPostIndex(BaseModel):
    objectID: str
    title: str = ''
    category: str = ''
    tags: list[str] = []
    content: str = ''
    # unsearchable attrs below
    relative_url: str
    created_time: int = 0
    updated_time: int = 0

    @classmethod
    def parse_content(cls, content: Content):
        # this method must be called under session open
        index = cls(
            objectID=str(content.id),
            title=content.title,
            created_time=int(datetime.timestamp(content.created_time)),
            updated_time=int(datetime.timestamp(content.updated_time)),
            relative_url=f'content/{content.id}'
        )
        if content.content is not None:
            index.content = base64.b64decode(content.content).decode()
        # must open database session in apis
        if content.category_id is not None:
            index.category = content.category.name
        if content.tags is not None:
            index.tags = [tag.name for tag in content.tags]
        return index
