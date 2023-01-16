from sqlalchemy.orm import Session
from models import PostCategory, PostTag, Resource
from schemas import ResourceQuery
from service import DatabaseService


class ResourceDao:
    @staticmethod
    @DatabaseService.database_session
    def get_sub_resources(parent_url: str | None = None,
                          resource_query: ResourceQuery = ResourceQuery(),
                          obj_class: any = Resource,
                          *, session: Session) -> list[any]:
        res = session.query(obj_class).order_by(obj_class.updated_time.desc())

        if parent_url is not None and len(parent_url) > 0:
            res = res.filter(obj_class.parent_url == parent_url)
        if resource_query.category_name is not None:
            res = res.join(PostCategory).filter(
                PostCategory.name == resource_query.category_name)
        if resource_query.tag_name is not None:
            res = res.filter(obj_class.tags.any(
                PostTag.name == resource_query.tag_name))
        if resource_query.page_size != 0:
            # res = res.offset(page_idx * page_size).limit(page_size)
            res = res.slice(resource_query.page_idx * resource_query.page_size,
                            (resource_query.page_idx + 1) * resource_query.page_size)

        session.commit()
        return res.all()

    @staticmethod
    @DatabaseService.database_session
    def get_sub_resource_count(parent_url: str | None = None,
                               resource_query: ResourceQuery = ResourceQuery(),
                               obj_class: any = Resource,
                               *, session: Session) -> int:
        res = session.query(obj_class)
        if parent_url is not None and len(parent_url) > 0:
            res = res.filter(obj_class.parent_url == parent_url)
        if resource_query.category_name is not None:
            res = res.join(PostCategory).filter(
                PostCategory.name == resource_query.category_name)
        if resource_query.tag_name is not None:
            res = res.filter(obj_class.tags.any(
                PostTag.name == resource_query.tag_name))
        session.commit()
        return res.count()
