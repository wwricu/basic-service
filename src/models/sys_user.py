from sqlalchemy import Column, String, LargeBinary
from sqlalchemy.orm import relationship

from .base_table import BaseTable


class SysUser(BaseTable):
    def __str__(self):
        return self.username
    __tablename__ = 'sys_user'
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(128), unique=True, nullable=False)
    password_hash = Column(LargeBinary(length=1024), nullable=False)

    resources = relationship("Resource", back_populates="owner")
    roles = relationship(
        'SysRole',
        secondary='user_role',
        back_populates='users',
        lazy="selectin"
    )


class SysRole(BaseTable):
    def __str__(self):
        return self.name if self.name else ''

    __tablename__ = 'sys_role'
    name = Column(String(20), unique=True, nullable=False)
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
        return self.name if self.name else ''
    __tablename__ = 'sys_permission'
    name = Column(String(20), unique=True, nullable=False)
    description = Column(String(255), comment="permission description")
    roles = relationship(
        'SysRole',
        secondary='role_permission',
        back_populates='permissions'
    )
