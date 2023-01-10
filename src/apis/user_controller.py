from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from schemas import UserInput, UserOutput
from service import UserService, DatabaseService
from .auth_controller import RequiresRoles


user_router = APIRouter(prefix="/user", tags=["user"])


@user_router.post("",
                  dependencies=[Depends(RequiresRoles('admin'))],
                  response_model=UserOutput)
async def add_user(user_input: UserInput,
                   db: Session = Depends(DatabaseService.get_db)):
    return UserService.add_user(db, user_input)


@user_router.get("/{user_id}",
                 dependencies=[Depends(RequiresRoles('admin'))],
                 response_model=list[UserOutput])
async def get_users(user_id: int = None,
                    username: str = None,
                    email: str = None,
                    db: Session = Depends(DatabaseService.get_db)):
    return UserService.find_user(
        db, UserInput(id=user_id,
                      username=username,
                      email=email)
    )


@user_router.put("",
                 dependencies=[Depends(RequiresRoles('admin'))],
                 response_model=UserOutput)
async def modify_users(user_input: UserInput,
                       db: Session = Depends(DatabaseService.get_db)):
    return UserService.modify_user(db, user_input)


@user_router.delete("/{user_id}",
                    dependencies=[Depends(RequiresRoles('admin'))],
                    response_model=int)
async def remove_users(user_id: int,
                       db: Session = Depends(DatabaseService.get_db)):
    return UserService.remove_user(db, UserInput(id=user_id))
