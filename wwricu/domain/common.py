from pydantic import BaseModel as PydanticBaseModel, ConfigDict


class BaseModel(PydanticBaseModel):
    model_config =  ConfigDict(from_attributes=True)


class HttpErrorDetail(object):
    POST_NOT_FOUND: str = 'Post Not Found'
    NO_SUCH_USER: str = 'NO SUCH USER'
    WRONG_PASSWORD: str = 'WRONG PASSWORD'
    NOT_AUTHORIZED: str = 'Not authorized'
    UPLOAD_FAILURE: str = 'Failed to upload'
    INVALID_TAG_TYPE: str = 'Invalid tag type'


class CommonConstant(object):
    SESSION_ID: str = 'session_id'
    SESSION_SIGN: str = 'sign'
    EXPIRE_TIME: int = 60 * 60 * 24 * 7
    APP_TITLE: str = 'wwr.icu'
    APP_VERSION: str = 'v2.0.0'
    CONFIG_PATH: str = 'conf/config.json'
    TOKEN_PATH: str = 'conf/github_token.txt'
    STORE_RET_KEY: str = 'key'


class EntityConstant(object):
    USER_STRING_LEN: int = 64
    ENUM_STRING_LEN: int = 32


class ConfigCenterConst(object):
    URL: str = 'https://api.github.com/repos/wwricu/config/contents/config.json'
    ACCEPT: str = 'application/vnd.github+json'
    AUTHORIZATION: str = 'Bearer {token}'
    TOKEN_KEY: str = 'github_token'
