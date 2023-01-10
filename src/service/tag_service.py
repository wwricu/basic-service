from sqlalchemy.orm import Session

from models import Tag
from dao import BaseDao


class TagService:
    @staticmethod
    def add_tag(db: Session, tag: Tag) -> Tag:
        return BaseDao.insert(tag, db)

    @staticmethod
    def find_tag(db: Session, tag: Tag) -> list[Tag]:
        return BaseDao.select(tag, tag.__class__, db)

    @staticmethod
    def rename_tag(db: Session, tag: Tag) -> Tag:
        return BaseDao.update(tag, tag.__class__, db)

    @staticmethod
    def remove_tag(db: Session, tag: Tag) -> int:
        return BaseDao.delete(tag, tag.__class__, db)
