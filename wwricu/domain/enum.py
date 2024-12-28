from enum import StrEnum


class TagTypeEnum(StrEnum):
    POST_TAG: str = 'post_tag'
    POST_CAT: str = 'post_category'


class PostStatusEnum(StrEnum):
    PUBLISHED = 'published'
    DRAFT = 'draft'


class PostResourceTypeEnum(StrEnum):
    MD: str = 'markdown'
    IMAGE: str = 'image'
    HTML: str = 'html'


class RelationTypeEnum(StrEnum):
    POST_TAG: str = 'post_tag'
    POST_RES: str = 'post_resource'
