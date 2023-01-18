from sqlalchemy import Table
from typing import Type
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from .async_database import AsyncDatabase


class BaseDao:
    @staticmethod
    @AsyncDatabase.database_session
    async def insert(obj: Table, *, session: AsyncSession):
        session.add(obj)
        await session.commit()
        return obj

    @staticmethod
    @AsyncDatabase.database_session
    async def insert_all(obj: list[Table], *, session: AsyncSession):
        session.add_all(obj)
        await session.commit()

    @staticmethod
    @AsyncDatabase.database_session
    async def select(obj: any,
                     class_name: Table | Type,
                     *, session: AsyncSession):
        statement = select(class_name)

        for key in class_name.__dict__:
            if key[0] == '_' or not hasattr(obj, key):
                continue
            attr = getattr(obj, key)
            if attr is None:
                continue
            if isinstance(attr, int) or isinstance(attr, str):
                statement = statement.where(getattr(class_name, key) == attr)
        return (await session.scalars(statement)).all()

    @staticmethod
    @AsyncDatabase.database_session
    async def update(obj: any,
                     class_name: Table | Type,
                     *, session: AsyncSession):
        if obj.id is None or obj.id == 0:
            return

        origin_obj = await session.scalar(
            select(class_name).where(getattr(class_name, 'id') == obj.id)
        )
        for key in obj.__dict__:
            if key[0] == '_' or getattr(obj, key) is None:
                continue
            # TODO: change relations on update
            attr = getattr(obj, key)
            if not isinstance(attr, list):
                setattr(origin_obj, key, attr)
        await session.commit()
        return origin_obj

    @staticmethod
    @AsyncDatabase.database_session
    async def delete(obj: any,
                     class_name: Table | Type,
                     *, session: AsyncSession):
        if obj.id is None or obj.id == 0:
            return
        obj = await session.scalar(
            select(class_name).where(getattr(class_name, 'id') == obj.id)
        )
        await session.delete(obj)
        await session.commit()

    @staticmethod
    @AsyncDatabase.database_session
    async def delete_all(objs: list,
                         class_name: Table | Type,
                         *, session: AsyncSession):
        for obj in objs:
            obj = await BaseDao.select(obj, class_name)
            if len(obj) == 1:
                await session.delete(obj[0])
        await session.commit()
