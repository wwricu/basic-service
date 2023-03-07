from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base_table import BaseTable


class Tag(BaseTable):
    __tablename__ = 'tag'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.name


class PostTag(Tag):
    def __init__(
        self,
        name: str | None = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.name = name

    __tablename__ = 'post_tag'
    id = Column(
        Integer,
        ForeignKey('tag.id', ondelete='CASCADE'),
        primary_key=True
    )
    name = Column(String(128), unique=True)

    posts = relationship(
        'Content',
        secondary='post_tag_relation',
        back_populates='tags'
    )
    __mapper_args__ = {
        'polymorphic_identity': 'post_tag',
        'inherit_condition': id == Tag.id,
    }


class PostCategory(Tag):
    def __init__(
        self,
        name: str | None = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.name = name

    __tablename__ = 'post_category'
    id = Column(
        Integer,
        ForeignKey('tag.id', ondelete='CASCADE'),
        primary_key=True
    )
    name = Column(String(128), unique=True)

    posts = relationship('Content', back_populates='category')
    __mapper_args__ = {
        'polymorphic_identity': 'post_category',
        'inherit_condition': id == Tag.id,
    }
