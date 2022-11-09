from pydantic import BaseModel
from typing import Any

from .user import UserInfo, AuthInfo


class Response(BaseModel):
    data: Any = None
    status: str
    message: str = None
