import json


class Config:
    db_url = 'mariadb+pymysql://root:153226@127.0.0.1:3306/fastdb?charset=utf8'
    admin_username = 'wwr'
    admin_password_hash = 'f5168b16e387802b06e95905727277b0'
    admin_password_salt = 'CrvV5IDnCZ2noa-f4a_KChCBac284vBAw11p_NsiKa4'
    admin_email = 'iswangwr@gmail.com'
    jwt_secret = '245700b63ff9720127a531a1da7841b54582e0729f59505800b2f689f0d43788'

    @classmethod
    def read_config(cls, filename: str = 'assets/config.json'):
        try:
            with open(filename, 'r') as f:
                config_text = f.read()
                config_json = json.loads(config_text)
                Config.load_config(**config_json)
            print(f'read {filename}')
        except FileNotFoundError:
            print('use dev config')

    @classmethod
    def load_config(cls,
                    db_url: str,
                    admin_username: str,
                    admin_password_hash: str,
                    admin_password_salt: str,
                    admin_email: str,
                    jwt_secret: str):
        cls.db_url = db_url
        cls.admin_username = admin_username
        cls.admin_password_hash = admin_password_hash
        cls.admin_password_salt = admin_password_salt
        cls.admin_email = admin_email
        cls.jwt_secret = jwt_secret
