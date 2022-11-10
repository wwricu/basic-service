from dao import UserDao
from schemas import UserInput, UserOutput
from models import SysUser
from .security_service import SecurityService


class UserService:
    @staticmethod
    def user_login(auth_info: UserInput):
        sys_user = UserDao.query_users(auth_info)[0]

        if not SecurityService\
                .verify_password(auth_info.password,
                                 sys_user.salt,
                                 sys_user.password_hash):
            raise Exception('Password Mismatch')

        return UserOutput(id=sys_user.id,
                          username=sys_user.username,
                          email=sys_user.email,
                          roles=[x.name for x in sys_user.roles])

    @staticmethod
    def add_user(auth_info: UserInput):
        sys_user = SysUser(id=auth_info.id,
                           username=auth_info.username,
                           email=auth_info.email)

        sys_user.salt = SecurityService.generate_salt()
        sys_user.password_hash = SecurityService.\
            get_password_hash(auth_info.password,
                              sys_user.salt)

        sys_user = UserDao.insert_user(sys_user)

        return UserOutput(id=sys_user.id,
                          username=sys_user.username,
                          email=sys_user.email)

    @staticmethod
    def find_user(user_info: UserOutput):

        users = map(lambda it: UserOutput(id=it.id,
                                          username=it.username,
                                          email=it.email,
                                          roles=[x.name for x in it.roles]),
                    UserDao.query_users(user_info))
        return list(users)

    @staticmethod
    def modify_user(auth_info: UserInput):
        sys_user = UserDao.query_users(auth_info)[0]

        sys_user.username = auth_info.username
        sys_user.email = auth_info.email
        sys_user.password_hash = SecurityService \
            .get_password_hash(auth_info.password,
                               sys_user.salt)

        return UserDao.update_user(sys_user)

    @staticmethod
    def remove_user(auth_info: UserInput):
        return UserDao.delete_user(SysUser(id=auth_info.id))