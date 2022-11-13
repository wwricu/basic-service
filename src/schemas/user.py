from pydantic import BaseModel


class UserInput(BaseModel):
    id: int = None
    username: str = None
    password: str = None
    email: str = None


class UserOutput(BaseModel):
    @classmethod
    def init(cls, sys_user):
        return UserOutput(id=sys_user.id,
                          username=sys_user.username,
                          email=sys_user.email,
                          roles=[x.name for x in sys_user.roles])

    id: int = None
    username: str = None
    email: str = None
    roles: list[str] = None
