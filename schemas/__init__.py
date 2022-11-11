from pydantic import BaseModel
from typing import Any

from .user import UserOutput, UserInput
from .resource import ContentInput, ContentOutput, FolderInput, FolderOutput, ResourceBase


class Response(BaseModel):
    data: Any = None
    status: str
    message: str = None


class Request(BaseModel):
    data: Any = None
