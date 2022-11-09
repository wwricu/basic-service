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

    return UserInfo(id=sys_user.id,
                    username=sys_user.username,
                    email=sys_user.email)


@alchemy_session
def add_user(auth_info: AuthInfo, db):
    sys_user = SysUser(id=auth_info.id,
                       username=auth_info.username,
                       email=auth_info.email)

    sys_user.salt = generate_salt()
    sys_user.password_hash = get_password_hash(auth_info.password,
                                               sys_user.salt)

    db.add(sys_user)
    db.flush()
    db.commit()

    return UserInfo(id=sys_user.id,
                    username=sys_user.username,
                    email=sys_user.email)


@alchemy_session
def find_user(user_info: UserInfo, db):
    res = db.query(SysUser)

    if user_info.id != 0:
        res = res.filter(SysUser.id == user_info.id)
    if user_info.username is not None:
        res = res.filter(SysUser.username == user_info.username)
    if user_info.email is not None:
        res = res.filter(SysUser.email == user_info.email)

    users = map(lambda it: UserInfo(id=it.id,
                                    username=it.username,
                                    email=it.email,
                                    roles=[x.name for x in it.roles]),
                res.all())
    return list(users)
