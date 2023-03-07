import hashlib
from threading import Lock

from fastapi import FastAPI, Request
from jwt import InvalidTokenError
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend

from dao import AsyncDatabase
from config import Config, logger
from models import (
    Content,
    PostCategory,
    PostTag,
    SysRole,
    SysUser,
)
from schemas import UserOutput
from service import SecurityService


class ContentAdmin(ModelView, model=Content):
    column_list = [
        Content.title,
        Content.parent,
        Content.category,
        Content.tags,
        Content.group,
        Content.permission
    ]
    column_details_list = column_list
    form_columns = column_list


class SysRoleAdmin(ModelView, model=SysRole):
    column_list = [
        SysRole.id,
        SysRole.name,
        SysRole.users
    ]
    column_details_list = column_list
    form_columns = column_list


class SysUserAdmin(ModelView, model=SysUser):
    column_list = [
        SysUser.id,
        SysUser.username,
        SysUser.email,
        SysUser.roles
    ]
    column_details_list = column_list
    form_columns = [
        SysUser.id,
        SysUser.username,
        SysUser.password_hash,
        SysUser.email,
        SysUser.roles
    ]
    column_labels = {SysUser.password_hash: "Password"}

    async def on_model_change(
        self,
        data: dict,
        model: any,
        is_created: bool
    ) -> None:
        data['password_hash'] = SecurityService.get_password_hash(
            hashlib.sha256(
                data['password_hash'].encode()
            ).hexdigest().encode()
        )


class PostCategoryAdmin(ModelView, model=PostCategory):
    column_list = [PostCategory.name]
    column_details_list = column_list
    form_columns = column_list
    can_view_details = False


class PostTagAdmin(ModelView, model=PostTag):
    column_list = [PostTag.name]
    column_details_list = column_list
    form_columns = column_list
    can_view_details = False


class SqlAdmin(AuthenticationBackend):
    __admin: Admin = None
    __lock: Lock = Lock()

    async def login(self, request: Request) -> bool:
        form = await request.form()

        user_output: UserOutput = await SecurityService.user_login(
            form["username"],
            hashlib.sha256(form["password"].encode()).hexdigest().encode()
        )
        request.session.update({
            'access_token': SecurityService.create_jwt_token(
                user_output, Config.jwt.key, hours=1
            )
        })
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get('access_token')
        try:
            SecurityService.verify_jwt_token(token, Config.jwt.key)
        except InvalidTokenError:
            return False
        return True

    @classmethod
    async def init(cls, fastapi_app: FastAPI) -> Admin:
        cls.__lock.acquire()
        if cls.__admin is not None:
            cls.__lock.release()
            return cls.__admin

        cls.__admin = Admin(
            app=fastapi_app,
            engine=await AsyncDatabase.get_engine(),
            authentication_backend=cls(secret_key=Config.jwt.key)
        )
        for view in (
            ContentAdmin,
            PostCategoryAdmin,
            PostTagAdmin,
            SysRoleAdmin,
            SysUserAdmin,
        ):
            cls.__admin.add_view(view)
        cls.__lock.release()
        logger.info('sqladmin inited')
        return cls.__admin
