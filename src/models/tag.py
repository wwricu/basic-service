from sqlalchemy import Integer, Column, String, ForeignKey
from sqlalchemy.orm import relationship

from . import Base


class Tag(Base):
    @classmethod
    def init(cls, tag_schema):
        if tag_schema is None:
            return None
        return Tag(id=tag_schema.id,
                   name=tag_schema.name)

    __tablename__ = 'tag'
    id = Column(Integer, primary_key=True, autoincrement=True)


class PostTag(Tag):
    __tablename__ = 'post_tag'
    id = Column(Integer,
                ForeignKey('tag.id', ondelete='CASCADE'),
                primary_key=True)
    name = Column(String(128), unique=True)

    posts = relationship('Content',
                         secondary='post_tag_relation',
                         back_populates='tags')
    __mapper_args__ = {
        'polymorphic_identity': 'post_tag',
        'inherit_condition': id == Tag.id,
    }


class PostCategory(Tag):
    __tablename__ = 'post_category'
    id = Column(Integer,
                ForeignKey('tag.id', ondelete='CASCADE'),
                primary_key=True)
    name = Column(String(128), unique=True)

    posts = relationship('Content',
                         back_populates='category')
    __mapper_args__ = {
        'polymorphic_identity': 'post_category',
        'inherit_condition': id == Tag.id,
    }
