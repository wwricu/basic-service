from enum import IntEnum, StrEnum


class HttpErrorDetail(StrEnum):
    POST_NOT_FOUND = 'Post Not Found'
    WRONG_PASSWORD = 'WRONG PASSWORD'
    WRONG_TOTP = 'WRONG TOTP'
    NEED_TOTP = 'Please input TOTP'
    NOT_AUTHORIZED = 'Not authorized'
    UNKNOWN_ENTITY_TYPE = 'Unknown entity type'
    CONFIG_NOT_ALLOWED = 'Cannot get this config'
    NO_TOTP_SECRET = 'No totp secret'
    INVALID_VALUE = 'Invalid value'
    TOO_MANY_REQUESTS = 'Too many requests'


class CommonConstant(StrEnum):
    SESSION_ID_2FA = '2fa_session_id'
    SESSION_ID = 'session_id'
    COOKIE_SIGN = 'sign'
    APP_NAME = 'wwr.icu'
    COMMON_ERROR = 'Internal Server Error'
    GLOBAL_TOKEN_BUCKET_ID = 'global'
    IMG_TAG = 'img'
    SRC_PROP = 'src'
    HTML_PARSER = 'html.parser'


class TimeConstant(IntEnum):
    COOKIE_MAX_AGE = 7 * 24 * 60 * 60
    ONE_DAY_SECONDS = 60 * 60 * 24
    TOTP_EXPIRATION = 300
    CACHE_EXPIRATION = 600


class HttpHeader(StrEnum):
    X_REAL_IP = 'X-Real-IP'
    X_FORWARD_FOR = 'X-Forwarded-For'
