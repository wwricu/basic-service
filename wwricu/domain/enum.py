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


class DatabaseActionEnum(StrEnum):
    BACKUP: str = 'backup'
    RESTORE: str = 'restore'


class EnvironmentEnum(StrEnum):
    LOCAL: str = 'local'
    DEVELOPMENT: str = 'development'
    PRODUCTION: str = 'production'


class ConfigKeyEnum(StrEnum):
    ABOUT_CONTENT: str = 'about_content'
    ABOUT_AVATAR: str = 'about_avatar'
    TOTP_SECRET: str = 'totp_secret'
    USERNAME: str = 'username'
    PASSWORD: str = 'password'
