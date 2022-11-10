from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from service import SecurityService, UserService
from schemas import Response, UserInput

from .user_controller import user_router
from .auth_controller import auth_router

router = APIRouter()
router.include_router(user_router)
router.include_router(auth_router)


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user_output = UserService \
            .user_login(UserInput(username=form_data.username,
                                  password=form_data.password))
        jwt = SecurityService.create_access_token(user_output)
        return {"access_token": jwt, "token_type": "bearer"}
    except Exception as e:
        return Response(status='failure',
                        message=e.__str__())