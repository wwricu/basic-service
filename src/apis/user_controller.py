from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from schemas import UserInput, UserOutput
from service import UserService
from core.dependency import RequiresRoles, get_db


user_router = APIRouter(prefix="/user", tags=["user"])


@user_router.post("", response_model=UserOutput)
async def add_user(user_input: UserInput,
                   db: Session = Depends(get_db),
                   cur_user: UserOutput = Depends(RequiresRoles('admin'))):
    return UserService.add_user(user_input, db)


@user_router.get("/{user_id}", response_model=list[UserOutput])
async def get_users(user_id: int = None,
                    username: str = None,
                    email: str = None,
                    db: Session = Depends(get_db),
                    cur_user: UserOutput = Depends(RequiresRoles('admin'))):
    return UserService.find_user(UserInput(id=user_id,
                                           username=username,
                                           email=email), db)


@user_router.put("", response_model=UserOutput)
async def modify_users(user_input: UserInput,
                       db: Session = Depends(get_db),
                       cur_user: UserOutput = Depends(RequiresRoles('admin'))):
    return UserService.modify_user(user_input, db)


@user_router.delete("/{user_id}", response_model=int)
async def remove_users(user_id: int,
                       db: Session = Depends(get_db),
                       cur_user: UserOutput = Depends(RequiresRoles('admin'))):
    return UserService.remove_user(UserInput(id=user_id), db)
