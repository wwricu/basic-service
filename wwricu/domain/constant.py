from enum import StrEnum


class HttpErrorDetail(StrEnum):
    POST_NOT_FOUND = 'Post Not Found'
    WRONG_PASSWORD = 'WRONG PASSWORD'
    WRONG_TOTP = 'WRONG TOTP'
    LOGIN_FORBIDDEN = 'LOGIN FORBIDDEN'
    NEED_TOTP = 'Please input TOTP'
    NOT_AUTHORIZED = 'Not authorized'
    LOGIN_TIMEOUT = 'Login Timeout'
    UNKNOWN_ENTITY_TYPE = 'Unknown entity type'
    CONFIG_NOT_ALLOWED = 'Cannot get this config'
    NO_TOTP_SECRET = 'No totp secret'
    INVALID_VALUE = 'Invalid value'
    TOO_MANY_REQUESTS = 'Too many requests'


class CommonConstant:
    SESSION_ID: str = 'session_id'
    COOKIE_SIGN: str = 'sign'
    APP_NAME: str = 'wwr.icu'
    COMMON_ERROR: str = 'Internal Server Error'
    COOKIE_MAX_AGE: int = 7 * 24 * 60 * 60
    ONE_DAY_SECONDS: int = 60 * 60 * 24
