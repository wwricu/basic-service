class HttpErrorDetail:
    POST_NOT_FOUND: str = 'Post Not Found'
    NO_SUCH_USER: str = 'NO SUCH USER'
    WRONG_PASSWORD: str = 'WRONG PASSWORD'
    WRONG_TOTP: str = 'WRONG TOTP'
    NEED_TOTP: str = 'Please input TOTP'
    NOT_AUTHORIZED: str = 'Not authorized'
    UPLOAD_FAILURE: str = 'Failed to upload'
    INVALID_TAG_TYPE: str = 'Invalid tag type'
    UNKNOWN_ENTITY_TYPE: str = 'Unknown entity type'
    LENGTH_EXCEEDED: str = 'Length exceeded'
    CONFIG_NOT_ALLOWED: str = 'Cannot get this config'
    NO_TOTP_SECRET: str = 'No totp secret'
    INVALID_VALUE: str = 'Invalid value'


class CommonConstant:
    SESSION_ID: str = 'session_id'
    COOKIE_SIGN: str = 'sign'
    APP_NAME: str = 'wwr.icu'
    COOKIE_MAX_AGE: int = 7 * 24 * 60 * 60
