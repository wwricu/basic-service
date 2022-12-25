from sqlalchemy.orm import Session

from models import Tag, ResourceTag
from dao import BaseDao


class TagService:
    @staticmethod
    def add_tag(tag: Tag, db: Session) -> Tag:
        return BaseDao.insert(tag, db)

    @staticmethod
    def find_tag(tag: Tag, db: Session) -> list[Tag]:
        return BaseDao.select(tag, tag.__class__, db)

    @staticmethod
    def rename_tag(tag: Tag, db: Session):
        return BaseDao.update(tag, tag.__class__, db)

    @staticmethod
    def remove_tag(tag: Tag, db: Session):
        return BaseDao.delete(tag, tag.__class__, db)
