from sqlalchemy.orm import Session

from models import Tag
from dao import BaseDao


class TagService:
    @staticmethod
    def add_tag(db: Session, tag: Tag) -> Tag:
        return BaseDao.insert(db, tag)

    @staticmethod
    def find_tag(db: Session, tag: Tag) -> list[Tag]:
        return BaseDao.select(db, tag, tag.__class__)

    @staticmethod
    def rename_tag(db: Session, tag: Tag) -> Tag:
        return BaseDao.update(db, tag, tag.__class__)

    @staticmethod
    def remove_tag(db: Session, tag: Tag) -> int:
        return BaseDao.delete(db, tag, tag.__class__)
