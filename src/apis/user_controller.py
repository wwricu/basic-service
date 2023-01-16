from fastapi import APIRouter, Depends

from schemas import UserInput, UserOutput
from service import UserService, DatabaseService
from .auth_controller import RequiresRoles


user_router = APIRouter(prefix="/user",
                        tags=["user"],
                        dependencies=[Depends(RequiresRoles('admin')),
                                      Depends(DatabaseService.open_session)])


@user_router.post("", response_model=UserOutput)
async def add_user(user_input: UserInput):
    return UserService.add_user(user_input)


@user_router.get("/{user_id}", response_model=list[UserOutput])
async def get_users(user_input: UserInput = Depends()):
    return UserService.find_user(user_input)


@user_router.put("", response_model=UserOutput)
async def modify_users(user_input: UserInput):
    return UserService.modify_user(user_input)


@user_router.delete("/{user_id}", response_model=int)
async def remove_users(user_id: int):
    return UserService.remove_user(UserInput(id=user_id))
