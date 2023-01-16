from models import Tag
from dao import BaseDao


class TagService:
    @staticmethod
    def add_tag(tag: Tag) -> Tag:
        return BaseDao.insert(tag)

    @staticmethod
    def find_tag(tag: Tag) -> list[Tag]:
        return BaseDao.select(tag, tag.__class__)

    @staticmethod
    def rename_tag(tag: Tag) -> Tag:
        return BaseDao.update(tag, tag.__class__)

    @staticmethod
    def remove_tag(tag: Tag) -> int:
        return BaseDao.delete(tag, tag.__class__)
