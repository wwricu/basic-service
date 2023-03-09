from sqlalchemy import Boolean, Column, String, LargeBinary
from sqlalchemy.orm import relationship

from .base_table import BaseTable


class SysUser(BaseTable):
    def __init__(
        self,
        username: str | None = None,
        email: str | None = None,
        password_hash: bytes | None = None,
        two_fa_enforced: bool | None = False,
        totp_key: str | None = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.two_fa_enforced = two_fa_enforced
        self.totp_key = totp_key

    def __str__(self):
        return self.username

    __tablename__ = 'sys_user'
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(128), unique=True, nullable=False)
    password_hash = Column(LargeBinary(length=1024), nullable=False)

    two_fa_enforced = Column(Boolean, nullable=False, default=False)
    totp_key = Column(String(64), nullable=True)  # 64 length base32 string

    resources = relationship("Resource", back_populates="owner")
    roles = relationship(
        'SysRole',
        secondary='user_role',
        back_populates='users',
        lazy="selectin"
    )


class SysRole(BaseTable):
    def __init__(
        self,
        name: str | None = None,
        description: str | None = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.name = name
        self.description = description

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
    def __init__(
        self,
        name: str | None = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.name = name

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
