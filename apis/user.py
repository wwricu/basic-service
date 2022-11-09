from fastapi import APIRouter

from schemas import AuthInfo, Response, UserInfo
from core import alchemy_session


user_router = APIRouter(prefix="/user")


@user_router.post("/auth", response_model=Response)
@alchemy_session
async def login(auth_info: AuthInfo, db):
    print(auth_info.dict())
    user_info = UserInfo()
    res = Response(data=user_info, status='success')
    return res
