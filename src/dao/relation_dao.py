from typing import Optional
from models import Content, Tag


class RelationDao:
    @staticmethod
    def get_contents_by_parent_tag(db,
                                   parent_id: Optional[int] = 0,
                                   status: Optional[str] = None,
                                   tag_id: Optional[int] = 0,
                                   page_idx:  Optional[int] = 0,
                                   page_size:  Optional[int] = 0):
        res = db.query(Content).order_by(Content.created_time.desc())

        if parent_id != 0:
            res = res.filter(Content.parent_id == parent_id)
        if status is not None:
            res = res.filter(Content.status == status)
        if tag_id != 0:
            res = res.filter(Content.tags.any(Tag.id == tag_id))
        if page_size != 0:
            # res = res.offset(page_idx * page_size).limit(page_size)
            res = res.slice(page_idx * page_size, (page_idx + 1) * page_size)

        db.commit()
        return res.all()

    @staticmethod
    def get_content_count(db,
                          parent_id: Optional[int] = 0,
                          status: Optional[str] = None,
                          tag_id: Optional[int] = 0):
        res = db.query(Content)
        if parent_id != 0:
            res = res.filter(Content.parent_id == parent_id)
        if status is not None:
            res = res.filter(Content.status == status)
        if tag_id != 0:
            res = res.filter(Content.tags.any(Tag.id == tag_id))
        db.commit()
        return res.count()
