from models import Content, Tag


class RelationDao:
    @staticmethod
    def get_contents_by_parent_tag(parent_id: int, tag_id: int, db):
        res = db.query(Content)
        if parent_id is not None and parent_id != 0:
            res = res.filter(Content.parent_id == parent_id)
        if tag_id is not None and tag_id != 0:
            res = res.filter(Content.tags.any(Tag.id == tag_id))
        db.commit()
        return res.all()
