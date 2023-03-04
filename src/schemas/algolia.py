from __future__ import annotations
from datetime import datetime

from pydantic import BaseModel

from models import Content


class AlgoliaPostIndex(BaseModel):
    objectID: int
    title: str = ''
    category: str = ''
    tags: list[str] = []
    # unsearchable attrs below
    created_time: int = 0
    updated_time: int = 0

    @classmethod
    def parse_content(cls, content: Content):
        # this method must be called under session open
        index = cls(
            objectID=content.id,
            title=content.title,
            created_time=int(datetime.timestamp(content.created_time)),
            updated_time=int(datetime.timestamp(content.updated_time)),
        )
        if content.category_id is not None:
            index.category = content.category.name
        if content.tags is not None:
            index.tags = [tag.name for tag in content.tags]
        return index
