from dao import UserDao
from schemas import AuthInfo, UserInfo
from models import SysUser
from .security_service import SecurityService


class UserService:
    @staticmethod
    def user_login(auth_info: AuthInfo):
        sys_user = UserDao.query_users(auth_info).first()

        if not SecurityService\
                .verify_password(auth_info.password,
                                 sys_user.salt,
                                 sys_user.password_hash):
            raise Exception('Password Mismatch')

        return UserInfo(id=sys_user.id,
                        username=sys_user.username,
                        email=sys_user.email)

    @staticmethod
    def add_user(auth_info: AuthInfo):
        sys_user = SysUser(id=auth_info.id,
                           username=auth_info.username,
                           email=auth_info.email)

        sys_user.salt = SecurityService.generate_salt()
        sys_user.password_hash = SecurityService.\
            get_password_hash(auth_info.password,
                              sys_user.salt)

        sys_user = UserDao.insert_user(sys_user)

        return UserInfo(id=sys_user.id,
                        username=sys_user.username,
                        email=sys_user.email)

    @staticmethod
    def find_user(user_info: UserInfo):

        users = map(lambda it: UserInfo(id=it.id,
                                        username=it.username,
                                        email=it.email,
                                        roles=[x.name for x in it.roles]),
                    UserDao.query_users(user_info))
        return list(users)
