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


class RelationTypeEnum(StrEnum):
    POST_TAG = 'post_tag'


class DatabaseActionEnum(StrEnum):
    BACKUP = 'backup'
    RESTORE = 'restore'


class EnvironmentEnum(StrEnum):
    DEVELOPMENT = 'dev'
    PRODUCTION = 'prod'


class ConfigKeyEnum(StrEnum):
    ABOUT_CONTENT = 'about_content'
    SITE_TITLE = 'site_title'
    SITE_TAGLINE = 'site_tagline'
    TOTP_ENFORCE = 'totp_enforce'
    TOTP_SECRET = 'totp_secret'
    USERNAME = 'username'
    PASSWORD = 'password'


class ManageCommandEnum(StrEnum):
    SET_ABOUT = 'set_about'
    SET_SITE_TITLE = 'set_site_title'
    SET_SITE_TAGLINE = 'set_site_tagline'
    SET_LOGIN = 'set_login'
    RESET_LOGIN = 'reset_login'
    ENROLL_TOTP = 'enroll_totp'
    CONFIRM_TOTP = 'confirm_totp'
    DISABLE_TOTP = 'disable_totp'
    REBUILD_SEARCH_INDEX = 'rebuild_search_index'


class CacheKeyEnum(StrEnum):
    POST_COUNT = 'post_count'
    CATEGORY_COUNT = 'category_count'
    TAG_COUNT = 'tag_count'
    CONFIG = 'config:{key}'
    POST = 'post:{id}'
    ALL_POSTS = 'all_posts:{page_index}:{page_size}:{category}:{tag_list}'
    ALL_TAGS = 'all_tags:{type}'


class EntityTypeEnum(StrEnum):
    BLOG_POST = 'Post'
    POST_TAG = 'Tag'
    POST_CAT = 'Category'
    POST_IMAGE = 'Image'
    POST_COVER = 'Cover'
