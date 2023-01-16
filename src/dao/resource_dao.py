from sqlalchemy.orm import Session
from models import PostCategory, PostTag
from service import DatabaseService


class ResourceDao:
    @staticmethod
    @DatabaseService.database_session
    def get_sub_resources(obj_class: any,
                          parent_url: str | None = None,
                          category_name: str | None = None,
                          tag_name: str | None = None,
                          page_idx:  int | None = 0,
                          page_size:  int | None = 0,
                          *, session: Session) -> list[any]:
        res = session.query(obj_class).order_by(obj_class.updated_time.desc())

        if parent_url is not None and len(parent_url) > 0:
            res = res.filter(obj_class.parent_url == parent_url)
        if category_name is not None:
            res = res.join(PostCategory).filter(PostCategory.name == category_name)
        if tag_name is not None:
            res = res.filter(obj_class.tags.any(PostTag.name == tag_name))
        if page_size != 0:
            # res = res.offset(page_idx * page_size).limit(page_size)
            res = res.slice(page_idx * page_size, (page_idx + 1) * page_size)

        session.commit()
        return res.all()

    @staticmethod
    @DatabaseService.database_session
    def get_sub_resource_count(obj_class: any,
                               parent_url: str | None = None,
                               category_name: str | None = None,
                               tag_name: str | None = None,
                               *, session: Session) -> int:
        res = session.query(obj_class)
        if parent_url is not None and len(parent_url) > 0:
            res = res.filter(obj_class.parent_url == parent_url)
        if category_name is not None:
            res = res.join(PostCategory).filter(PostCategory.name == category_name)
        if tag_name is not None:
            res = res.filter(obj_class.tags.any(PostTag.name == tag_name))
        session.commit()
        return res.count()
