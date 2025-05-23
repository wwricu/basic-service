import os
from enum import StrEnum


class TagTypeEnum(StrEnum):
    POST_TAG = 'post_tag'
    POST_CAT = 'post_category'


class PostStatusEnum(StrEnum):
    PUBLISHED = 'published'
    DRAFT = 'draft'


class PostResourceTypeEnum(StrEnum):
    IMAGE = 'image'
    COVER_IMAGE = 'cover'
    COMMON = 'common'


class RelationTypeEnum(StrEnum):
    POST_TAG = 'post_tag'
    POST_RES = 'post_resource'


class EnvironmentEnum(StrEnum):
    LOCAL = 'local'
    DEVELOPMENT = 'dev'
    PRODUCTION = 'prod'


class ConfigKeyEnum(StrEnum):
    ABOUT_CONTENT = 'about_content'
    TOTP_ENFORCE = 'totp_enforce'
    TOTP_SECRET = 'totp_secret'
    USERNAME = 'username'
    PASSWORD = 'password'


class CacheKeyEnum(StrEnum):
    POST_COUNT = 'post_count'
    CATEGORY_COUNT = 'category_count'
    TAG_COUNT = 'tag_count'
    LOGIN_LOCK = 'login_lock'
    LOGIN_RETRIES = 'login_retries'
    STARTUP_TIMESTAMP = 'startup_timestamp'


class EntityTypeEnum(StrEnum):
    BLOG_POST = 'blog_post'
    POST_TAG = 'post_tag'
    POST_CAT = 'post_category'


class EnvVarEnum(StrEnum):
    ENV = EnvironmentEnum.LOCAL.value
    ROOT_PATH = '/'
    LOG_PATH = 'logs'
    CONFIG_FILE = 'config.json'

    def get(self) -> str:
        return os.getenv(self.name, self.value)
