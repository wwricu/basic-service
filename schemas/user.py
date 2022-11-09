from pydantic import BaseModel
from typing import List


class AuthInfo(BaseModel):
    id: int = None
    username: str = None
    password: str = None
    email: str = None


class UserInfo(BaseModel):
    id: int = None
    username: str = None
    email: str = None
    roles: List[str] = None
