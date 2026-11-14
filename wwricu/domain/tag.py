from typing import Annotated

from pydantic import Field, StringConstraints

from wwricu.domain.common import BaseModel
from wwricu.domain.enum import PostStatusEnum, TagTypeEnum


class TagRO(BaseModel):
    id: int | None = None
    name: Annotated[str, StringConstraints(max_length=32)]
    type: TagTypeEnum | None = TagTypeEnum.POST_TAG


class TagRequestRO(BaseModel):
    type: TagTypeEnum | None = TagTypeEnum.POST_TAG


class TagQueryDTO(BaseModel):
    tag_ids: list[int] | None = None
    name: str | None = None
    type: TagTypeEnum | None = None
    deleted: bool | None = False


class TagVO(BaseModel):
    id: int
    name: str
    type: TagTypeEnum
    count: int = 0


class TagUpdateDTO(BaseModel):
    tag_id_list: list[int] = Field(default_factory=list)
    category_id: int | None = None
    status: PostStatusEnum
