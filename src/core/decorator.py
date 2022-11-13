import functools

from service import DatabaseService


def alchemy_session(method):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        db = DatabaseService.get_session()
        db.expire_on_commit = False
        return method(*args, db, **kwargs)
    return wrapper
