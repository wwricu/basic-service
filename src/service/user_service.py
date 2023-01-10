from sqlalchemy.orm import Session
from dao import BaseDao
from schemas import UserInput, UserOutput
from models import SysUser
from .security_service import SecurityService


class UserService:
    @staticmethod
    def user_login(db: Session, user_input: UserInput) -> UserOutput:
        sys_user = BaseDao.select(user_input, SysUser, db)[0]

        if not SecurityService\
                .verify_password(user_input.password,
                                 sys_user.salt,
                                 sys_user.password_hash):
            raise Exception('Password Mismatch')

        return UserOutput.init(sys_user)

    @staticmethod
    def add_user(db: Session, user_input: UserInput) -> UserOutput:
        sys_user = SysUser(id=user_input.id,
                           username=user_input.username,
                           email=user_input.email)

        sys_user.salt = SecurityService.generate_salt()
        sys_user.password_hash = SecurityService.\
            get_password_hash(user_input.password,
                              sys_user.salt)

        return UserOutput.init(BaseDao.insert(sys_user, db))

    @staticmethod
    def find_user(db: Session, user_input: UserInput) -> list[UserOutput]:
        return list(map(lambda it: UserOutput.init(it),
                        BaseDao.select(user_input, SysUser, db)))

    @staticmethod
    def modify_user(db: Session, user_input: UserInput) -> UserOutput:
        sys_user = BaseDao.select(SysUser(id=user_input.id), SysUser, db)[0]

        if user_input.username is not None:
            sys_user.username = user_input.username
        if user_input.email is not None:
            sys_user.email = user_input.email
        if user_input.password is not None:
            sys_user.password_hash = SecurityService \
                .get_password_hash(user_input.password,
                                   sys_user.salt)

        BaseDao.update(sys_user, SysUser, db)
        return UserOutput.init(sys_user)

    @staticmethod
    def remove_user(db: Session, user_input: UserInput) -> int:
        return BaseDao.delete(SysUser(id=user_input.id), SysUser, db)
