from enum import StrEnum


class TagTypeEnum(StrEnum):
    POST_TAG: str = 'post_tag'
    POST_CAT: str = 'post_category'


class PostStatusEnum(StrEnum):
    PUBLISHED = 'published'
    DRAFT = 'draft'


class PostResourceTypeEnum(StrEnum):
    IMAGE: str = 'image'
    COVER_IMAGE: str = 'cover'
    COMMON: str = 'common'


class RelationTypeEnum(StrEnum):
    POST_TAG: str = 'post_tag'
    POST_RES: str = 'post_resource'
