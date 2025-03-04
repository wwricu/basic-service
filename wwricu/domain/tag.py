from __future__ import annotations

from wwricu.domain.common import BaseModel
from wwricu.domain.enum import TagTypeEnum


class TagRO(BaseModel):
    id: int | None = None
    name: str
    type: TagTypeEnum | None = TagTypeEnum.POST_TAG


class TagRequestRO(BaseModel):
    page_size: int | None = 0
    page_index: int | None = 0
    type: TagTypeEnum | None = TagTypeEnum.POST_TAG


class TagVO(BaseModel):
    id: int
    name: str
    type: TagTypeEnum
    count: int | None = None
