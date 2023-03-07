from fastapi import FastAPI
from sqladmin import Admin, ModelView

from .async_database import AsyncDatabase


from models import (
    SysUser,
)


class SysUserAdmin(ModelView, model=SysUser):
    column_list = [
        SysUser.id,
        SysUser.username,
        SysUser.email,
        SysUser.roles
    ]
    column_formatters = {
        SysUser.roles: lambda sys_user, a: [r.name for r in sys_user.roles]
    }

    column_details_list = [
        SysUser.id,
        SysUser.username,
        SysUser.email,
        SysUser.roles
    ]
    column_formatters_detail = {
        SysUser.roles: lambda sys_user, a: [r.name for r in sys_user.roles]
    }

    form_columns = [
        SysUser.username,
        SysUser.email,
        SysUser.roles
    ]


async def init_admin(app: FastAPI):
    admin = Admin(app, await AsyncDatabase.get_engine())
    views = (
        SysUserAdmin,
    )
    for view in views:
        admin.add_view(view)
