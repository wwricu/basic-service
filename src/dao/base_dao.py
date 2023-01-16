from sqlalchemy import Table
from sqlalchemy.orm import Session
from typing import Type
from service import DatabaseService


class BaseDao:
    @staticmethod
    @DatabaseService.database_session
    def get_query(obj: Table,
                  class_name: Table | Type,
                  *, session: Session):
        res = session.query(class_name)

        for key in class_name.__dict__:
            if key[0] == '_' or not hasattr(obj, key):
                continue
            attr = getattr(obj, key)
            if attr is None:
                continue
            if isinstance(attr, int) or isinstance(attr, str):
                res = res.filter(getattr(class_name, key) == attr)
        return res

    @staticmethod
    @DatabaseService.database_session
    def insert(obj: Table, *, session: Session):
        session.add(obj)
        session.commit()
        return obj

    @staticmethod
    @DatabaseService.database_session
    def insert_all(obj: list[Table], *, session: Session):
        session.add_all(obj)
        session.commit()

    @staticmethod
    @DatabaseService.database_session
    def select(obj: any,
               class_name: Table | Type,
               *, session: Session):
        res = BaseDao.get_query(obj, class_name).all()
        session.commit()
        return res

    @staticmethod
    @DatabaseService.database_session
    def update(obj: any,
               class_name: Table | Type,
               *, session: Session):
        if obj.id is None or obj.id == 0:
            return

        origin_obj = session.query(class_name).filter_by(id=obj.id).one()
        for key in obj.__dict__:
            if key[0] == '_' or getattr(obj, key) is None:
                continue
            # TODO: change relations on update
            attr = getattr(obj, key)
            if not isinstance(attr, list):
                setattr(origin_obj, key, attr)
        session.commit()
        return origin_obj

    @staticmethod
    @DatabaseService.database_session
    def delete(obj: any,
               class_name: Table | Type,
               *,
               session: Session):
        if obj.id is None or obj.id == 0:
            return
        count = session.query(class_name).filter_by(id=obj.id).delete()
        session.commit()
        return count

    @staticmethod
    @DatabaseService.database_session
    def delete_all(objs: list,
                   class_name: Table | Type,
                   *, session: Session):
        count = 0
        for obj in objs:
            count += BaseDao.get_query(obj, class_name).delete()
        session.commit()
        return count
