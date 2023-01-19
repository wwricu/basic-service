import json
from anyio import Path


class DatabaseConfig:
    def __init__(self,
                 drivername: str | None = 'mariadb+aiomysql',
                 username: str | None = 'root',
                 password: str | None = '153226',
                 host: str | None = '127.0.0.1',
                 port: int | None = 3306,
                 database: str | None = 'fastdb'):
        self.drivername = drivername
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.database = database


class Config:
    admin_username = 'wwr'
    admin_password_hash = 'f5168b16e387802b06e95905727277b0'
    admin_password_salt = 'CrvV5IDnCZ2noa-f4a_KChCBac284vBAw11p_NsiKa4'
    admin_email = 'iswangwr@gmail.com'
    jwt_secret = '245700b63ff9720127a531a1da7841b54582e0729f59505800b2f689f0d43788'
    database: DatabaseConfig = DatabaseConfig()

    @classmethod
    async def read_config(cls, filename: str = 'assets/config.json'):
        try:
            config_text = await Path(filename).read_text()
            config_json = json.loads(config_text)
            cls.load_json(**config_json)
            print(f'read {filename}')
        except FileNotFoundError:
            print('use dev config')

    @classmethod
    def load_json(cls,
                  admin_username: str,
                  admin_password_hash: str,
                  admin_password_salt: str,
                  admin_email: str,
                  jwt_secret: str,
                  database: dict):
        cls.admin_username = admin_username
        cls.admin_password_hash = admin_password_hash
        cls.admin_password_salt = admin_password_salt
        cls.admin_email = admin_email
        cls.jwt_secret = jwt_secret
        cls.database = DatabaseConfig(**database)
