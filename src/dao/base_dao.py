class BaseDao:
    @staticmethod
    def get_query(obj, class_name, db):
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
    def insert(obj, db):
        db.add(obj)
        db.commit()
        # db.refresh(obj)
        # db.expunge(obj)
        return obj

    @staticmethod
    def insert_all(obj, db):
        db.add_all(obj)
        db.commit()

    @staticmethod
    def select(obj, class_name, db):
        res = BaseDao.get_query(obj, class_name, db).all()
        db.commit()
        return res

    @staticmethod
    def update(obj, class_name, db):
        if obj.id is None or obj.id == 0:
            return

        origin_obj = db.query(class_name) \
                       .filter_by(id=obj.id).one()
        for key in obj.__dict__:
            if key[0] == '_' or getattr(obj, key) is None:
                continue
            # if key != '_sa_instance_state':
            setattr(origin_obj, key, getattr(obj, key))
        db.commit()
        return origin_obj

    @staticmethod
    def delete(obj, class_name, db):
        if obj.id is None or obj.id == 0:
            return
        count = db.query(class_name) \
                  .filter_by(id=obj.id) \
                  .delete()
        db.commit()
        return count

    @staticmethod
    def delete_all(objs, class_name, db):
        count = 0
        for obj in objs:
            count += BaseDao.get_query(obj, class_name, db).delete()
        db.commit()
        return count
