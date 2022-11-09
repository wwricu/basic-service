from pydantic import BaseModel


class UserInfo(BaseModel):
    id: int
    username: str = None
    password: str = None
    email: str = None
