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
    IMG_TAG = 'img'
    SRC_PROP = 'src'
    HTML_PARSER = 'html.parser'
    TOKEN_SEPARATOR = '\x01'
    MARK_BEGIN = '<mark>'
    MARK_END = '</mark>'


class TimeConst(IntEnum):
    ONE_MIN_SECONDS = 60
    ONE_HOUR_SECONDS = 60 * ONE_MIN_SECONDS
    ONE_DAY_SECONDS = 24 * ONE_HOUR_SECONDS
    COOKIE_MAX_AGE = 7 * ONE_DAY_SECONDS
    TOTP_EXPIRATION = 5 * ONE_MIN_SECONDS
    CACHE_EXPIRATION = 10 * ONE_MIN_SECONDS
