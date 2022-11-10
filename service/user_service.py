from dao import UserDao
from schemas import UserInput, UserOutput
from models import SysUser
from .security_service import SecurityService


class UserService:
    @staticmethod
    def user_login(user_input: UserInput):
        sys_user = UserDao.query_users(user_input)[0]

        if not SecurityService\
                .verify_password(user_input.password,
                                 sys_user.salt,
                                 sys_user.password_hash):
            raise Exception('Password Mismatch')

        return UserOutput(sys_user)

    @staticmethod
    def add_user(user_input: UserInput):
        sys_user = SysUser(id=user_input.id,
                           username=user_input.username,
                           email=user_input.email)

        sys_user.salt = SecurityService.generate_salt()
        sys_user.password_hash = SecurityService.\
            get_password_hash(user_input.password,
                              sys_user.salt)

        return UserOutput(UserDao.insert_user(sys_user))

    @staticmethod
    def find_user(user_input: UserInput):
        return list(map(lambda it: UserOutput(it),
                        UserDao.query_users(user_input)))

    @staticmethod
    def modify_user(user_input: UserInput):
        sys_user = UserDao.query_users(user_input)[0]

        sys_user.username = user_input.username
        sys_user.email = user_input.email
        sys_user.password_hash = SecurityService \
            .get_password_hash(user_input.password,
                               sys_user.salt)

        return UserOutput(UserDao.update_user(sys_user))

    @staticmethod
    def remove_user(user_input: UserInput):
        return UserOutput(UserDao.delete_user(SysUser(id=user_input.id)))
