from core.decorator import alchemy_session


class BaseDao:
    @staticmethod
    @alchemy_session
    def insert(obj, db):
        try:
            db.add(obj)
            db.commit()
            db.refresh(obj)
            db.expunge(obj)
            return obj
        finally:
            db.close()

    @staticmethod
    @alchemy_session
    def select(obj, class_name, db):
        try:
            res = db.query(class_name)

            for key in class_name.__dict__:
                if key[0] == '_':
                    continue
                if not hasattr(obj, key):
                    continue
                attr = getattr(obj, key)
                if attr is None:
                    continue
                if isinstance(attr, int) or isinstance(attr, str):
                    res = res.filter(getattr(class_name, key) == attr)

            return res.all()
        finally:
            db.close()

    @staticmethod
    @alchemy_session
    def update(obj, class_name, db):
        if obj.id is None or obj.id == 0:
            return

        try:
            origin_obj = db.query(class_name) \
                           .filter_by(id=obj.id).one()
            for key in obj.__dict__:
                if key[0] == '_' or getattr(obj, key) is None:
                    continue
                # if key != '_sa_instance_state':
                setattr(origin_obj, key, getattr(obj, key))

            db.commit()
        finally:
            db.close()

    @staticmethod
    @alchemy_session
    def delete(obj, class_name, db):
        if obj.id is None or obj.id == 0:
            return
        try:
            count = db.query(class_name) \
                      .filter_by(id=obj.id) \
                      .delete()
            db.commit()
            return count
        finally:
            db.close()
