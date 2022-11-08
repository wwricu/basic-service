from sqlalchemy import Integer, Column, String
from sqlalchemy.orm import relationship

from . import Base


class SysUser(Base):
    __tablename__ = 'sys_user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(20), unique=True, comment="username")
    password_hash = Column(String(128), comment="password hash")
    salt = Column(String(128), comment="salt")
    roles = relationship('sys_role', secondary='user_role')


class SysRole(Base):
    __tablename__ = 'sys_role'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), unique=True, comment="role name")
    description = Column(String(255), comment="role description")
    users = relationship('SysUser', secondary='UserRole')
    permissions = relationship('sys_permission', secondary='role_permission')


class SysPermission(Base):
    __tablename__ = 'sys_permission'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), unique=True, comment="permission name")
    description = Column(String(255), comment="permission description")
    roles = relationship('sys_role', secondary='role_permission')
