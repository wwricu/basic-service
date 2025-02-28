from wwricu.domain.common import BaseModel
from wwricu.domain.enum import ConfigKeyEnum, PostStatusEnum, TagTypeEnum


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


class LoginRO(BaseModel):
    username: str
    password: str
    captcha: str | None = None
    otp: str | None = None


class TagRO(BaseModel):
    id: int | None = None
    name: str
    type: TagTypeEnum | None = TagTypeEnum.POST_TAG


class TagRequestRO(BaseModel):
    page_size: int | None = 0
    page_index: int | None = 0
    type: TagTypeEnum | None = TagTypeEnum.POST_TAG


class ConfigRO(BaseModel):
    key: ConfigKeyEnum
    value: str | None = None
