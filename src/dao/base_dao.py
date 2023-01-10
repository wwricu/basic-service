from sqlalchemy import Table
from sqlalchemy.orm import Session
from typing import Type


class BaseDao:
    @staticmethod
    def get_query(db: Session, obj: Table, class_name: Table | Type):
        res = db.query(class_name)

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
    def insert(db: Session, obj: Table):
        db.add(obj)
        db.commit()
        return obj

    @staticmethod
    def insert_all(db: Session, obj: list[Table]):
        db.add_all(obj)
        db.commit()

    @staticmethod
    def select(db: Session, obj: any, class_name: Table | Type):
        res = BaseDao.get_query(db, obj, class_name).all()
        db.commit()
        return res

    @staticmethod
    def update(db: Session, obj: any, class_name: Table | Type):
        if obj.id is None or obj.id == 0:
            return

        origin_obj = db.query(class_name).filter_by(id=obj.id).one()
        for key in obj.__dict__:
            if key[0] == '_' or getattr(obj, key) is None:
                continue
            # TODO: change relations on update
            attr = getattr(obj, key)
            if not isinstance(attr, list):
                setattr(origin_obj, key, attr)
        db.commit()
        return origin_obj

    @staticmethod
    def delete(db: Session, obj: any, class_name: Table | Type):
        if obj.id is None or obj.id == 0:
            return
        count = db.query(class_name).filter_by(id=obj.id).delete()
        db.commit()
        return count

    @staticmethod
    def delete_all(db: Session, objs: list, class_name: Table | Type):
        count = 0
        for obj in objs:
            count += BaseDao.get_query(db, obj, class_name).delete()
        db.commit()
        return count
