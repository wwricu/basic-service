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
