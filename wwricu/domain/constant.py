from enum import IntEnum, StrEnum


class HttpErrorDetail(StrEnum):
    POST_NOT_FOUND = 'Post Not Found'
    WRONG_PASSWORD = 'Wrong Username or Password'
    WRONG_TOTP = 'Wrong TOTP'
    NEED_TOTP = 'Please input TOTP'


class CommonConst(StrEnum):
    SESSION_ID_2FA = '2fa_session_id'
    SESSION_ID = 'session_id'
    COOKIE_SIGN = 'sign'
    APP_NAME = 'wwr.icu'
    COMMON_ERROR = 'Internal Server Error'
    GLOBAL_TOKEN_BUCKET_ID = 'global'
    IMG_TAG = 'img'
    SRC_PROP = 'src'
    HTML_PARSER = 'html.parser'
    LOGIN_IP_BUCKET = 'login:{ip}'
    IMAGE_IP_BUCKET = 'image:{ip}'
    OPEN_IP_BUCKET = 'open:{ip}'


class TimeConst(IntEnum):
    COOKIE_MAX_AGE = 7 * 24 * 60 * 60
    ONE_DAY_SECONDS = 60 * 60 * 24
    TOTP_EXPIRATION = 300
    CACHE_EXPIRATION = 600
