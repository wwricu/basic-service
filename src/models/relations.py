from sqlalchemy import Column, ForeignKey, Integer

from .sys_user import Base


class UserRole(Base):
    __tablename__ = 'user_role'
    user_id = Column(
        Integer,
        ForeignKey('sys_user.id', ondelete='CASCADE'),
        primary_key=True
    )
    role_id = Column(
        Integer,
        ForeignKey('sys_role.id', ondelete='CASCADE'),
        primary_key=True
    )


class RolePermission(Base):
    __tablename__ = 'role_permission'
    role_id = Column(
        Integer,
        ForeignKey('sys_role.id', ondelete='CASCADE'),
        nullable=False,
        primary_key=True
    )
    permission_id = Column(
        Integer,
        ForeignKey('sys_permission.id', ondelete='CASCADE'),
        nullable=False,
        primary_key=True
    )


class ResourceTag(Base):
    __tablename__ = 'post_tag_relation'
    resource_id = Column(
        Integer,
        ForeignKey('content.id', ondelete='CASCADE'),
        nullable=False,
        primary_key=True
    )
    tag_id = Column(
        Integer,
        ForeignKey('post_tag.id', ondelete='CASCADE'),
        nullable=False,
        primary_key=True
    )
