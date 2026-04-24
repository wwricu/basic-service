from enum import StrEnum


class HttpErrorDetail(StrEnum):
    POST_NOT_FOUND = 'Post Not Found'
    NO_SUCH_USER = 'NO SUCH USER'
    WRONG_PASSWORD = 'WRONG PASSWORD'
    WRONG_TOTP = 'WRONG TOTP'
    NEED_TOTP = 'Please input TOTP'
    NOT_AUTHORIZED = 'Not authorized'
    LOGIN_TIMEOUT = 'Login Timeout'
    UPLOAD_FAILURE = 'Failed to upload'
    INVALID_TAG_TYPE = 'Invalid tag type'
    UNKNOWN_ENTITY_TYPE = 'Unknown entity type'
    LENGTH_EXCEEDED = 'Length exceeded'
    CONFIG_NOT_ALLOWED = 'Cannot get this config'
    NO_TOTP_SECRET = 'No totp secret'
    INVALID_VALUE = 'Invalid value'
    CONTENT_LENGTH = '{name} length range: {min_len} ~ {max_len}'


class CommonConstant:
    SESSION_ID: str = 'session_id'
    COOKIE_SIGN: str = 'sign'
    APP_NAME: str = 'wwr.icu'
    COMMON_ERROR: str = 'Internal Server Error'
    COOKIE_MAX_AGE: int = 7 * 24 * 60 * 60
    ONE_DAY_SECONDS: int = 60 * 60 * 24
