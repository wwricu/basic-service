from pydantic import BaseModel
from typing import Any

from .user import UserSchema, AuthSchema


class Response(BaseModel):
    data: Any = None
    status: str
    message: str = None
