from models import SysUser
from core.decorator import alchemy_session


class UserDao:
    @staticmethod
    @alchemy_session
    def insert_user(sys_user: SysUser, db):
        try:
            db.add(sys_user)
            db.flush()
            db.commit()
            return sys_user
        finally:
            db.close()

    @staticmethod
    @alchemy_session
    def query_users(sys_user: SysUser, db):
        try:
            res = db.query(SysUser)

            if sys_user.id is not None and sys_user.id != 0:
                res = res.filter(SysUser.id == sys_user.id)
            if sys_user.username is not None:
                res = res.filter(SysUser.username == sys_user.username)
            if sys_user.email is not None:
                res = res.filter(SysUser.email == sys_user.email)

            return res.all()
        finally:
            db.close()

    @staticmethod
    @alchemy_session
    def update_user(sys_user: SysUser, db):
        if sys_user.id is None or sys_user.id == 0:
            return

        try:
            sys_user = db.query(sys_user) \
                         .filter_by(id=sys_user.id) \
                         .update(sys_user)
            db.commit()
            return sys_user
        finally:
            db.close()

    @staticmethod
    @alchemy_session
    def delete_user(sys_user: SysUser, db):
        if sys_user.id is None or sys_user.id == 0:
            return

        try:
            sys_user = db.query(sys_user)\
                         .filter_by(id=sys_user.id)\
                         .delete()
            db.commit()
            return sys_user
        finally:
            db.close()
