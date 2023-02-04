from typing import Type, Sequence

from sqlalchemy import func, select, Table
from sqlalchemy.ext.asyncio import AsyncSession

from .async_database import AsyncDatabase
from models import PostCategory, PostTag, Resource
from schemas import ResourceQuery


class ResourceDao:
    @staticmethod
    @AsyncDatabase.database_session
    async def get_sub_resources(
            parent_url: str | None = None,
            resource_query: ResourceQuery = ResourceQuery(),
            obj_class: Table | Type = Resource,
            *, session: AsyncSession
    ) -> Sequence[any]:
        stmt = select(obj_class).order_by(obj_class.updated_time.desc())

        if parent_url is not None:
            stmt = stmt.where(obj_class.parent_url == parent_url)

        if resource_query.category_name is not None:
            stmt = stmt.join(PostCategory).where(
                PostCategory.name == resource_query.category_name
            )

        if resource_query.tag_name is not None:
            stmt = stmt.where(obj_class.tags.any(
                PostTag.name == resource_query.tag_name)
            )

        if resource_query.page_size != 0:
            # res = res.offset(page_idx * page_size).limit(page_size)
            stmt = stmt.slice(
                resource_query.page_idx * resource_query.page_size,
                (resource_query.page_idx + 1) * resource_query.page_size
            )

        return (await session.scalars(stmt)).all()

    @staticmethod
    @AsyncDatabase.database_session
    async def get_sub_resource_count(
            parent_url: str | None = None,
            resource_query: ResourceQuery = ResourceQuery(),
            obj_class: Table | Type = Resource,
            *, session: AsyncSession
    ) -> int:
        stmt = select(func.count()).select_from(obj_class)

        if parent_url is not None:
            stmt = stmt.where(obj_class.parent_url == parent_url)

        if resource_query.category_name is not None:
            stmt = stmt.join(PostCategory).where(
                PostCategory.name == resource_query.category_name
            )

        if resource_query.tag_name is not None:
            stmt = stmt.where(obj_class.tags.any(
                PostTag.name == resource_query.tag_name)
            )

        return await session.scalar(stmt)
