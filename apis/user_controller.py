from fastapi import APIRouter

from schemas import AuthSchema, UserSchema, Response
from service import UserService, SecurityService


user_router = APIRouter(prefix="/user")


@user_router.post("/auth", response_model=Response)
async def login(auth_info: AuthSchema):
    try:
        user_info = UserService.user_login(auth_info)
        jwt = SecurityService.create_access_token(user_info)
        data = [user_info, jwt]
        return Response(data=data,
                        status='success')
    except Exception as e:
        return Response(status='failure',
                        message=e.__str__())


@user_router.post("/", response_model=Response)
async def add_user(auth_info: AuthSchema):
    try:
        return Response(data=UserService.add_user(auth_info),
                        status='success')
    except Exception as e:
        return Response(status='failure',
                        message=e.__str__())


@user_router.put("/", response_model=Response)
async def modify_users(user_info: UserSchema):
    try:
        return Response(data=UserService
                        .find_user(UserSchema(id=user_id,
                                              username=username,
                                              email=email)),
                        status='success')
    except Exception as e:
        return Response(status='failure',
                        message=e.__str__())


@user_router.get("/{user_id}", response_model=Response)
async def get_users(user_id: int,
                    username: str = None,
                    email: str = None):
    try:
        return Response(data=UserService
                        .find_user(UserSchema(id=user_id,
                                              username=username,
                                              email=email)),
                        status='success')
    except Exception as e:
        return Response(status='failure',
                        message=e.__str__())
