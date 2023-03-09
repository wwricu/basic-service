import json
import logging
from enum import IntEnum
from types import MappingProxyType

from anyio import Path

from models import Folder


logger = logging.getLogger()


class Status(IntEnum):
    HTTP_440_MAIL_2FA_NEEDED: int = 440
    HTTP_441_TOTP_2FA_NEEDED: int = 441
    HTTP_442_2FA_FAILED: int = 442


class AdminConfig:
    def __init__(
        self,
        username: str,
        password: str,
        email: str,
        role: dict | None = MappingProxyType({'name': 'admin'}),
        two_fa_enforced: bool | None = False,
        totp_key: str | None = None
    ):
        self.username = username
        self.password = password
        self.email = email
        self.role = role
        self.two_fa_enforced = two_fa_enforced
        self.totp_key = totp_key


class AlgoliaConfig:
    def __init__(
        self,
        app_id: str,
        admin_key: str,
        index_name: str,
        search_key: str | None = None
    ):
        self.app_id = app_id
        self.admin_key = admin_key
        self.index_name = index_name
        self.search_key = search_key


class DatabaseConfig:
    def __init__(
        self,
        drivername: str,
        database: str,  # below can be omitted for sqlite
        username: str | None = None,
        password: str | None = None,
        host: str | None = None,
        port: int | None = None,
    ):
        self.drivername = drivername
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.database = database


class JWTConfig:
    def __init__(
        self,
        key: str,
        algorithm: str | None = 'HS256',
        headers: dict | None = MappingProxyType({
            'alg': 'HS256',
            'typ': 'JWT'
        })
    ):
        self.key = key
        self.algorithm = algorithm
        self.headers = headers


class MailConfig:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password


class MiddlewareConfig:
    def __init__(
        self,
        allow_origin_regex: str | None = 'https?://.*',
        allow_credentials: bool | None = True,
        allow_methods: list[str] | None = ('*',),
        allow_headers: list[str] | None = ('*',),
        expose_headers: list[str] | None = (
            "X-token-need-refresh",
            "X-content-id",
            "X-2fa-token"
        ),
    ):
        self.allow_origin_regex = allow_origin_regex
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods
        self.allow_headers = allow_headers
        self.expose_headers = expose_headers


class RedisConfig:
    def __init__(
        self,
        host: str,
        port: int = 6379
    ):
        self.host = host
        self.port = port


class StaticResource:
    def __init__(
        self,
        root_path: str | None = 'static',
        content_path: str | None = 'static/content'
    ):
        self.root_path = root_path
        self.content_path = content_path


class TwoFAConfig:
    def __init__(
        self,
        jwt_key: str,
        enforcement: bool | None = False,
    ):
        self.jwt_key = jwt_key
        self.enforcement = enforcement


class Config:
    admin: AdminConfig = None
    database: DatabaseConfig = None
    folders: list[Folder] = []
    jwt: JWTConfig = None
    static: StaticResource = None
    # compulsory above
    algolia: AlgoliaConfig = None
    mail: MailConfig = None
    middleware: MiddlewareConfig = None
    redis: RedisConfig = None
    two_fa: TwoFAConfig = None

    @classmethod
    async def init_config(cls, filename: str = 'assets/config.json'):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(levelname)s:     %(message)s'
        ))
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        try:
            config_text = await Path(filename).read_text()
            config_json = json.loads(config_text)
            cls.load_json(**config_json)
            logger.info(f'config read finished with {filename}')
        except FileNotFoundError:
            logger.info('config file NOT found')

    @classmethod
    def load_json(
        cls,
        admin: dict,
        database: dict,
        folders: dict,
        jwt: dict,
        static: dict,
        two_fa: dict,
        algolia: dict | None = None,
        middleware: dict | None = MappingProxyType({}),
        mail: dict | None = None,
        redis: dict | None = None,
        *args,
        **kwargs
    ):
        _, _ = args, kwargs
        cls.database = DatabaseConfig(**database)
        cls.admin = AdminConfig(**admin)
        cls.jwt = JWTConfig(**jwt)
        cls.static = StaticResource(**static)
        cls.two_fa = TwoFAConfig(**two_fa)

        if algolia is not None:
            cls.algolia = AlgoliaConfig(**algolia)
        for folder in folders:
            cls.folders.append(Folder(**folder))
        if mail is not None:
            cls.mail = MailConfig(**mail)
        cls.middleware = MiddlewareConfig(**middleware)
        if redis is not None:
            cls.redis = RedisConfig(**redis)
