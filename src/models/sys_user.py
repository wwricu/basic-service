from sqlalchemy import Column, String, LargeBinary
from sqlalchemy.orm import relationship

from .base_table import BaseTable


class SysUser(BaseTable):
    def __str__(self):
        return self.username
    __tablename__ = 'sys_user'
    username = Column(String(20), unique=True, comment="username")
    email = Column(String(128), unique=True, comment="email")
    password_hash = Column(LargeBinary(length=1024), comment="password hash")

    resources = relationship("Resource", back_populates="owner")
    roles = relationship(
        'SysRole',
        secondary='user_role',
        back_populates='users',
        lazy="selectin"
    )


class SysRole(BaseTable):
    def __str__(self):
        return self.name

    __tablename__ = 'sys_role'
    name = Column(String(20), unique=True, comment="role name")
    description = Column(String(255), comment="role description")

    resources = relationship("Resource", back_populates="group")

    users = relationship(
        'SysUser',
        secondary='user_role',
        back_populates='roles'
    )
    permissions = relationship(
        'SysPermission',
        secondary='role_permission',
        back_populates='roles',
        lazy="selectin"
    )


class SysPermission(BaseTable):
    def __str__(self):
        return self.name
    __tablename__ = 'sys_permission'
    name = Column(String(20), unique=True, comment="permission name")
    description = Column(String(255), comment="permission description")
    roles = relationship(
        'SysRole',
        secondary='role_permission',
        back_populates='permissions'
    )
