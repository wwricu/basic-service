from typing import Optional
from models import Content, Tag


class ResourceDao:
    @staticmethod
    def get_sub_resources(db,
                          obj_class,
                          parent_url: Optional[str] = None,
                          tag_id: Optional[int] = 0,
                          page_idx:  Optional[int] = 0,
                          page_size:  Optional[int] = 0) -> list[Content]:
        res = db.query(obj_class).order_by(obj_class.created_time.desc())

        if parent_url is not None:
            res = res.filter(obj_class.parent_url == parent_url)
        if tag_id != 0:
            res = res.filter(obj_class.tags.any(Tag.id == tag_id))
        if page_size != 0:
            # res = res.offset(page_idx * page_size).limit(page_size)
            res = res.slice(page_idx * page_size, (page_idx + 1) * page_size)

        db.commit()
        return res.all()

    @staticmethod
    def get_sub_resource_count(db,
                               obj_class,
                               parent_url: Optional[str] = None,
                               tag_id: Optional[int] = 0):
        res = db.query(obj_class)
        if parent_url is not None and len(parent_url) > 0:
            res = res.filter(obj_class.parent_url == parent_url)
        if tag_id != 0:
            res = res.filter(obj_class.tags.any(Tag.id == tag_id))
        db.commit()
        return res.count()

    @staticmethod
    def delete(obj, class_name, db):
        if obj.url is None:
            return
        count = db.query(class_name) \
            .filter_by(url=obj.url) \
            .delete()
        db.commit()
        return count