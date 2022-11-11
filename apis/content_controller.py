from models import Resource, Content, Folder
from fastapi import Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from service import SecurityService, UserService
from schemas import Response, UserInput, UserOutput
from core.dependency import requires_login
from dao import ResourceDao


content_router = APIRouter(prefix="/content")


@content_router.get("")
async def get_resource():
    content = Content(title='test',
                      url='',
                      sub_title='test sub',
                      status='draft',
                      content='<p>test</p>'.encode())

    ResourceDao.insert_resource(content)
