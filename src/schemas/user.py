from pydantic import BaseModel


class RoleSchema(BaseModel):
    @classmethod
    def init(cls, role):
        if role is None:
            return None
        return RoleSchema(id=role.id,
                          name=role.name)
    id: int = None
    name: str = None


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
                          roles=[RoleSchema.init(role) for role in sys_user.roles])

    id: int = None
    username: str = None
    email: str = None
    roles: list[RoleSchema] = None


class TokenResponse(BaseModel):
    access_token: str = None
    refresh_token: str = None
    token_type: str = 'bearer'
