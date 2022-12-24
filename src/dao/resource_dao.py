from typing import Optional
from models import Content, PostTag


class ResourceDao:
    @staticmethod
    def get_sub_resources(db,
                          obj_class,
                          parent_url: Optional[str] = None,
                          category_name: Optional[str] = None,
                          tag_name: Optional[str] = None,
                          page_idx:  Optional[int] = 0,
                          page_size:  Optional[int] = 0) -> list[Content]:
        res = db.query(obj_class).order_by(obj_class.created_time.desc())

        if parent_url is not None and len(parent_url) > 0:
            res = res.filter(obj_class.parent_url == parent_url)
        if tag_name is not None:
            res = res.filter(obj_class.tags.any(PostTag.name == tag_name))
        if category_name is not None:
            res = res.filter(obj_class.category_name == category_name)
        if page_size != 0:
            # res = res.offset(page_idx * page_size).limit(page_size)
            res = res.slice(page_idx * page_size, (page_idx + 1) * page_size)

        db.commit()
        return res.all()

    @staticmethod
    def get_sub_resource_count(db,
                               obj_class,
                               parent_url: Optional[str] = None,
                               category_name: Optional[str] = None,
                               tag_name: Optional[str] = None):
        res = db.query(obj_class)
        if parent_url is not None and len(parent_url) > 0:
            res = res.filter(obj_class.parent_url == parent_url)
        if category_name is not None:
            res = res.filter(obj_class.category_name == category_name)
        if tag_name is not None:
            res = res.filter(obj_class.tags.any(PostTag.name == tag_name))
        db.commit()
        return res.count()
