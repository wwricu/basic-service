class HttpErrorDetail(object):
    POST_NOT_FOUND: str = 'Post Not Found'
    NO_SUCH_USER: str = 'NO SUCH USER'
    WRONG_PASSWORD: str = 'WRONG PASSWORD'
    WRONG_TOTP: str = 'WRONG TOTP'
    NOT_AUTHORIZED: str = 'Not authorized'
    UPLOAD_FAILURE: str = 'Failed to upload'
    INVALID_TAG_TYPE: str = 'Invalid tag type'
    UNKNOWN_ENTITY_TYPE: str = 'Unknown entity type'
    LENGTH_EXCEEDED: str = 'Length exceeded'
    CONFIG_NOT_ALLOWED: str = 'Cannot get this config'


class CommonConstant(object):
    SESSION_ID: str = 'session_id'
    COOKIE_SIGN: str = 'sign'
    EXPIRE_TIME: int = 60 * 60 * 24 * 7
    APP_NAME: str = 'wwr.icu'
    COOKIE_TIMEOUT_SECOND: int = 30 * 24 * 60 * 60
