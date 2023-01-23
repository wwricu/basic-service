from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class SysUser(Base):
    __tablename__ = 'sys_user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(20), unique=True, comment="username")
    email = Column(String(128), unique=True, comment="email")
    password_hash = Column(String(128), comment="password hash")
    salt = Column(String(128), comment="salt")

    resources = relationship("Resource", back_populates="owner")
    roles = relationship(
        'SysRole',
        secondary='user_role',
        back_populates='users',
        lazy="selectin"
    )


class SysRole(Base):
    __tablename__ = 'sys_role'
    id = Column(Integer, primary_key=True, autoincrement=True)
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


class SysPermission(Base):
    __tablename__ = 'sys_permission'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), unique=True, comment="permission name")
    description = Column(String(255), comment="permission description")
    roles = relationship(
        'SysRole',
        secondary='role_permission',
        back_populates='permissions'
    )
