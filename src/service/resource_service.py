import uuid

from models import Resource, Folder
from dao import BaseDao


class ResourceService:
    @staticmethod
    def add_resource(resource: Resource, db):
        resource.url = ''
        if resource.parent_id is not None and resource.parent_id != 0:
            parent = BaseDao.select(Resource(id=resource.parent_id),
                                    Resource, db)[0]
            resource.url = parent.url

        if isinstance(resource, Folder):
            resource.url += '/' + resource.title
        else:
            resource.url += '/' + str(uuid.uuid4())

        return BaseDao.insert(resource, db)

    @staticmethod
    def find_resources(resource: Resource, db):
        return BaseDao.select(resource, resource.__class__, db)

    @staticmethod
    def modify_resource(resource: Resource, db):
        return BaseDao.update(resource, resource.__class__, db)

    @staticmethod
    def remove_resource(resource: Resource, db):
        BaseDao.delete(resource, Resource, db)
