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

    @staticmethod
    def modify_tag_content(tag_id: int,
                           add_content_ids: list[int],
                           remove_content_ids: list[int],
                           db: Session):
        if add_content_ids is not None and len(add_content_ids) != 0:
            add_content_tags = [ResourceTag(tag_id=tag_id,
                                            content_id=x)
                                for x in add_content_ids]
            BaseDao.insert_all(add_content_tags, db)

        if remove_content_ids is not None and len(remove_content_ids) != 0:
            remove_content_tags = [ResourceTag(tag_id=tag_id,
                                               content_id=x)
                                   for x in remove_content_ids]

            BaseDao.delete_all(remove_content_tags, ResourceTag, db)
