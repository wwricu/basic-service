from pydantic import BaseModel as PydanticBaseModel, ConfigDict


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(from_attributes=True)


class HttpErrorDetail(object):
    POST_NOT_FOUND: str = 'Post Not Found'
    NO_SUCH_USER: str = 'NO SUCH USER'
    WRONG_PASSWORD: str = 'WRONG PASSWORD'
    NOT_AUTHORIZED: str = 'Not authorized'
    UPLOAD_FAILURE: str = 'Failed to upload'
    INVALID_TAG_TYPE: str = 'Invalid tag type'


class CommonConstant(object):
    SESSION_ID: str = 'session_id'
    COOKIE_SIGN: str = 'sign'
    EXPIRE_TIME: int = 60 * 60 * 24 * 7
    APP_NAME: str = 'wwr.icu'
    APP_VERSION: str = 'v2.0.0'
    CONFIG_DIR: str = 'conf'
    CONFIG_FILE: str = 'config.json'
    TOKEN_FILE: str = 'github_token.txt'
    STORE_RET_KEY: str = 'key'
    COOKIE_TIMEOUT_SECOND: int = 30 * 24 * 60 * 60


class EntityConstant(object):
    ENUM_STRING_LEN: int = 32
    USER_STRING_LEN: int = 64
    LONG_STRING_LEN: int = 128


class LoginConstant(object):
    LOCK_TIME: int = 30 * 60
    MAX_TRY: int = 3
    TRY_TIMEOUT: int = 5 * 60
    FAILURE_TIME_KEY: str = 'login_failed_time'
    LOCK_KEY: str = 'login_lock_key'
