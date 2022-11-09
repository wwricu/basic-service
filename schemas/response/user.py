from pydantic import BaseModel
from typing import List


class UserInfo(BaseModel):
    id: int = None
    username: str = None
    email: str = None
    roles: List[str] = []
