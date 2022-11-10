from pydantic import BaseModel
from typing import List

from models import SysUser


class UserInput(BaseModel):
    id: int = None
    username: str = None
    password: str = None
    email: str = None


class UserOutput(BaseModel):
    def __init__(self, sys_user: SysUser):
        BaseModel.__init__(self)
        self.id = sys_user.id
        self.username = sys_user.username
        self.email = sys_user.email
        self.roles = [x.name for x in sys_user.roles]

    id: int = None
    username: str = None
    email: str = None
    roles: List[str] = None
