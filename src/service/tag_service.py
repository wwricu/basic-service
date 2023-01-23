from dao import BaseDao
from models import Tag


class TagService:
    @staticmethod
    async def add_tag(tag: Tag) -> Tag:
        return await BaseDao.insert(tag)

    @staticmethod
    async def find_tag(tag: Tag) -> list[Tag]:
        return await BaseDao.select(tag, tag.__class__)

    @staticmethod
    async def rename_tag(tag: Tag) -> Tag:
        return await BaseDao.update(tag, tag.__class__)

    @staticmethod
    async def remove_tag(tag: Tag) -> int:
        return await BaseDao.delete(tag, tag.__class__)
