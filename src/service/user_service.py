from .security_service import SecurityService
from dao import BaseDao
from models import SysUser
from schemas import UserInput, UserOutput


class UserService:
    @staticmethod
    async def user_login(
        user_input: UserInput,
    ) -> UserOutput:
        sys_user = (await BaseDao.select(user_input, SysUser))[0]

        assert SecurityService.verify_password(
            user_input.password,
            sys_user.password_hash
        ) is True

        return UserOutput.init(sys_user)

    @staticmethod
    async def add_user(user_input: UserInput) -> UserOutput:
        sys_user = SysUser(
            id=user_input.id,
            username=user_input.username,
            password_hash=SecurityService.get_password_hash(
                user_input.password
            ),
            email=user_input.email,
            roles=[]
        )

        return UserOutput.init(await BaseDao.insert(sys_user))

    @staticmethod
    async def find_user(user_input: UserInput) -> list[UserOutput]:
        return list(map(
            lambda it: UserOutput.init(it),
            await BaseDao.select(user_input, SysUser)
        ))

    @staticmethod
    async def modify_user(user_input: SysUser) -> UserOutput:
        sys_user = (await BaseDao.select(
            SysUser(id=user_input.id), SysUser
        ))[0]

        if user_input.password_hash is not None:
            sys_user.password_hash = SecurityService.get_password_hash(
                user_input.password_hash
            )

        return UserOutput.init(await BaseDao.update(user_input, SysUser))

    @staticmethod
    async def remove_user(user_input: UserInput) -> int:
        return await BaseDao.delete(SysUser(id=user_input.id), SysUser)
