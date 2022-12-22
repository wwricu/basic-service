import uuid
from typing import Optional

from models import Resource, Folder, ResourceTag, Content
from dao import BaseDao, RelationDao
from schemas import UserOutput


class ResourceService:
    @staticmethod
    def add_resource(resource: Resource, db):
        resource.url = ''
        if resource.parent_url is not None:
            parent = BaseDao.select(Resource(url=resource.parent_url),
                                    Resource, db)[0]
            resource.url = parent.url

        if isinstance(resource, Folder):
            resource.this_url = '/' + resource.title
        else:
            resource.this_url = '/' + str(uuid.uuid4())
        resource.url += resource.this_url

        return BaseDao.insert(resource, db)

    @staticmethod
    def find_resources(resource: Resource, db):
        return BaseDao.select(resource, resource.__class__, db)

    @staticmethod
    def find_sub_resources(db,
                           obj_class = Resource,
                           parent_url: str = None,
                           tag_id: Optional[int] = 0,
                           page_idx: Optional[int] = 0,
                           page_size: Optional[int] = 0):
        return RelationDao.get_sub_resources(db,
                                             obj_class,
                                             parent_url,
                                             tag_id,
                                             page_idx,
                                             page_size)

    @staticmethod
    def find_sub_count(db,
                       obj_class = Resource,
                       parent_url: Optional[str] = None,
                       tag_id: Optional[int] = 0) -> int:
        return RelationDao.get_sub_resource_count(db,
                                                  obj_class,
                                                  parent_url,
                                                  tag_id)

    @staticmethod
    def modify_resource(resource: Resource, db):
        return BaseDao.update(resource, resource.__class__, db)

    @staticmethod
    def remove_resource(resource: Resource, db):
        BaseDao.delete(resource, Resource, db)

    @staticmethod
    def reset_content_tags(content: Content, db):
        BaseDao.delete_all([ResourceTag(content_id=content.id)], ResourceTag, db)
        add_content_tags = [ResourceTag(content_id=content.id,
                                        tag_id=x.id)
                            for x in content.tags]
        if len(add_content_tags) > 0:
            BaseDao.insert_all(add_content_tags, db)

    @staticmethod
    def check_permission(resource: Resource, user: UserOutput, operation_mask: int):
        permission = resource.permission % 10

        if user is not None:
            for role in user.roles:
                if role.name == 'admin':
                    return True
                if role.name == resource.group.name:
                    permission |= (resource.permission // 10) % 10
                    break
            if user.id == resource.owner_id:
                permission |= (resource.permission // 100) % 10

        if operation_mask & permission == 0:
            raise Exception('no permission')
        return True

    @staticmethod
    def modify_content_tags(resource_id: int,
                            add_tag_ids: list[int],
                            remove_tag_ids: list[int],
                            db):
        if add_tag_ids is not None and len(add_tag_ids) != 0:
            add_content_tags = [ResourceTag(content_id=resource_id,
                                            tag_id=x)
                                for x in add_tag_ids]
            BaseDao.insert_all(add_content_tags, db)

        if remove_tag_ids is not None and len(remove_tag_ids) != 0:
            remove_content_tags = [ResourceTag(content_id=resource_id,
                                               tag_id=x)
                                   for x in remove_tag_ids]
            BaseDao.delete_all(remove_content_tags, ResourceTag, db)
