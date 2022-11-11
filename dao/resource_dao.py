from models import Resource, Content, Folder
from core.decorator import alchemy_session


class ResourceDao:
    @staticmethod
    @alchemy_session
    def insert_resource(resource: Resource, db):
        try:
            db.add(resource)
            db.commit()
            db.refresh(resource)
            db.expunge(resource)
            return resource
        finally:
            db.close()

    @staticmethod
    @alchemy_session
    def select_resources(resource: Resource, db):
        try:
            res = db.query(resource)

            if resource.url is not None:
                res = res.filter(Resource.url == resource.url)
            if resource.id is not None and resource.id != 0:
                res = res.filter(Resource.id == resource.id)
            if resource.title is not None:
                res = res.filter(Resource.title == resource.title)

            return res.all()
        finally:
            db.close()
