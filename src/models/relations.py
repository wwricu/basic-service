from sqlalchemy import Integer, Column, ForeignKey

from . import Base


class UserRole(Base):
    __tablename__ = 'user_role'
    user_id = Column(
        Integer,
        ForeignKey('sys_user.id'),
        primary_key=True)
    role_id = Column(
        Integer,
        ForeignKey('sys_role.id'),
        primary_key=True)


class RolePermission(Base):
    __tablename__ = 'role_permission'
    role_id = Column(
        Integer,
        ForeignKey('sys_role.id'),
        nullable=False,
        primary_key=True)
    permission_id = Column(
        Integer,
        ForeignKey('sys_permission.id'),
        nullable=False,
        primary_key=True)
