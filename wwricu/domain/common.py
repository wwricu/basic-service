from __future__ import annotations

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field

from wwricu.domain.enum import ConfigKeyEnum


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRO(BaseModel):
    username: str
    password: str
    captcha: str | None = None
    otp: str | None = None


class ConfigRO(BaseModel):
    key: ConfigKeyEnum
    value: str | None = None


class PageVO[T](BaseModel):
    page_index: int
    page_size: int
    count: int
    post_details: list[T] = Field(default_factory=list)


class FileUploadVO(BaseModel):
    id: int
    name: str
    key: str
    location: str


class AboutPageVO(BaseModel):
    content: str | None = None
    post_count: int = 0
    category_count: int = 0
    tag_count: int = 0
