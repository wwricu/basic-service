from fastapi import APIRouter

from schemas import AuthInfo, Response
from core.user import user_login, add_user


user_router = APIRouter(prefix="/user")


@user_router.post("/auth", response_model=Response)
async def login(auth_info: AuthInfo):
    try:
        return Response(data=user_login(auth_info),
                        status='success')
    except Exception as e:
        return Response(status='failure',
                        message=e.__str__())


@user_router.post("/add", response_model=Response)
async def post_user(auth_info: AuthInfo):
    try:
        return Response(data=add_user(auth_info),
                        status='success')
    except Exception as e:
        return Response(status='failure',
                        message=e.__str__())
