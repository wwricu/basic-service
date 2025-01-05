from datetime import datetime

from botocore.response import StreamingBody
from loguru import logger as log
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
    COOKIE_SIGN: str = 'sign'
    EXPIRE_TIME: int = 60 * 60 * 24 * 7
    APP_TITLE: str = 'wwr.icu'
    APP_VERSION: str = 'v2.0.0'
    CONFIG_PATH: str = 'conf/config.json'
    TOKEN_PATH: str = 'conf/github_token.txt'
    STORE_RET_KEY: str = 'key'
    COOKIE_TIMEOUT_SECOND: int = 30 * 24 * 60 * 60


class EntityConstant(object):
    ENUM_STRING_LEN: int = 32
    USER_STRING_LEN: int = 64
    LONG_STRING_LEN: int = 128


class ConfigCenterConst(object):
    URL: str = 'https://api.github.com/repos/wwricu/config/contents/config.json'
    ACCEPT: str = 'application/vnd.github+json'
    AUTHORIZATION: str = 'Bearer {token}'
    TOKEN_KEY: str = 'github_token'


class AmazonS3ResponseMetaData(BaseModel):
    RequestId: str
    HostId: str
    HTTPStatusCode: int
    HTTPHeaders: dict


class AmazonS3Response(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, from_attributes=True)
    ResponseMetadata: dict
    AcceptRanges: str
    LastModified: datetime
    ContentLength: int
    ETag: str
    ContentType: str
    ServerSideEncryption: str
    Metadata: dict
    ResponseMetadata: dict
    Body: StreamingBody


class GithubContentResponse(BaseModel):
    name: str
    content: str
    download_url: str


def retry(max_try: int = 3):
    def decorator(func: callable):
        def wrapper(*args, **kwargs):
            t = max_try
            while True:
                try:
                    t -= 1
                    return func(*args, **kwargs)
                except Exception as e:
                    if t == 0:
                        raise e
                    log.info(f'{func.__name__} retry {max_try - t} times')
        return wrapper
    return decorator
