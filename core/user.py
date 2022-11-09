from core import alchemy_session
from schemas import AuthInfo, UserInfo
from models import SysUser
from .security import verify_password, generate_salt, get_password_hash


@alchemy_session
def user_login(auth_info: AuthInfo, db):
    sys_user = db.query(SysUser)\
                 .filter(SysUser.username == auth_info.username)\
                 .one()

    if not verify_password(auth_info.password,
                           sys_user.salt,
                           sys_user.password_hash):
        raise Exception('Password Mismatch')

    return sys_user


@alchemy_session
def add_user(auth_info: AuthInfo, db):
    sys_user = SysUser(id=auth_info.id,
                       username=auth_info.username,
                       email=auth_info.email)

    sys_user.salt = generate_salt()
    sys_user.password_hash = get_password_hash(auth_info.password,
                                               sys_user.salt)

    print(sys_user.password_hash)
    print(sys_user.salt)

    db.add(sys_user)
    db.flush()
    db.commit()

    return sys_user
