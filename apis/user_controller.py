from fastapi import APIRouter, Depends

from schemas import UserInput, UserOutput
from service import UserService
from core.dependency import RequiresRoles


user_router = APIRouter(prefix="/user")


@user_router.post("", response_model=UserOutput)
async def add_user(user_input: UserInput,
                   cur_user: UserOutput = Depends(RequiresRoles('admin'))):
    return UserService.add_user(user_input)


@user_router.get("/{user_id}", response_model=list[UserOutput])
async def get_users(user_id: int,
                    username: str = None,
                    email: str = None,
                    cur_user: UserOutput = Depends(RequiresRoles('admin'))):
    return UserService.find_user(UserInput(id=user_id,
                                           username=username,
                                           email=email))


@user_router.put("", response_model=UserOutput)
async def modify_users(user_input: UserInput,
                       cur_user: UserOutput = Depends(RequiresRoles('admin'))):
    return UserService.modify_user(user_input)


@user_router.delete("/{user_id}", response_model=int)
async def remove_users(user_id: int,
                       cur_user: UserOutput = Depends(RequiresRoles('admin'))):
    return UserService.remove_user(UserInput(id=user_id))
