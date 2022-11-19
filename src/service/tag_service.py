from sqlalchemy.orm import Session

from models import Tag, Content, ContentTag
from dao import BaseDao


class TagService:
    @staticmethod
    def add_tag(tag: Tag, db: Session) -> Tag:
        db.add(tag)
        db.commit()
        return tag

    @staticmethod
    def find_tag(tag: Tag, db: Session) -> list[Tag]:
        res = db.query(Tag)
        if tag.id != 0:
            res = res.filter(Tag.id == tag.id)
        if tag.name is not None:
            res = res.filter(Tag.name == tag.name)

        return res.all()

    @staticmethod
    def modify_tag(tag: Tag, db: Session):
        return BaseDao.update(tag, Tag)

    @staticmethod
    def remove_tag(tag: Tag, db: Session):
        return BaseDao.delete(tag, Tag)

    @staticmethod
    def modify_tag_content(tag: Tag,
                           add_contents: list[Content],
                           remove_contents: list[Content]):
        BaseDao.insert()
        return BaseDao.delete(tag, Tag)
