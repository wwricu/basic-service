from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from service import SecurityService, UserService
from schemas import Response, UserInput

from .user_controller import user_router
from .auth_controller import auth_router

router = APIRouter()
router.include_router(user_router)
router.include_router(auth_router)
