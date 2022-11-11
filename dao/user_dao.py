from models import SysUser
from core.decorator import alchemy_session


class UserDao:
    @staticmethod
    @alchemy_session
    def insert_user(sys_user: SysUser, db):
        try:
            db.add(sys_user)
            db.commit()
            db.refresh(sys_user)
            db.expunge(sys_user)
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
            origin_user = db.query(SysUser).filter_by(id=sys_user.id).one()
            if sys_user.username is not None:
                origin_user.username = sys_user.username
            if sys_user.username is not None:
                origin_user.email = sys_user.email
            if sys_user.password_hash is not None:
                origin_user.password_hash = sys_user.password_hash
            db.commit()
        finally:
            db.close()

    @staticmethod
    @alchemy_session
    def delete_user(sys_user: SysUser, db):
        if sys_user.id is None or sys_user.id == 0:
            return
        try:
            count = db.query(SysUser)\
                      .filter_by(id=sys_user.id)\
                      .delete()
            db.commit()
            return count
        finally:
            db.close()
