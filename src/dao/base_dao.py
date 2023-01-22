import asyncio
from typing import Type

from sqlalchemy import select, Table
from sqlalchemy.ext.asyncio import AsyncSession

from .async_database import AsyncDatabase


# TODO: use instance instead of static methods
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
        stmt = select(class_name)

        for key in class_name.__dict__:
            if key[0] == '_' or not hasattr(obj, key):
                continue
            attr = getattr(obj, key)
            if attr is None:
                continue
            if isinstance(attr, int) or isinstance(attr, str):
                stmt = stmt.where(getattr(class_name, key) == attr)
        '''
        NOTICE: Difference between session.scalars and session.scalar:
        scalar return the unique result as a raw OBJECT, while
        scalars returns multiple results that need further processing,
        so we must use '.all()', '.first()' or '.one()',
        to fetch result(s) from them.
        '''
        return (await session.scalars(stmt)).all()

    @staticmethod
    @AsyncDatabase.database_session
    async def update(obj: any,
                     class_name: Table | Type,
                     *, session: AsyncSession):
        if obj.id is None or obj.id == 0:
            return

        obj_update = await session.get(class_name, obj.id)
        # obj_update = await session.scalar(
        #     select(class_name).filter_by(id=obj.id)
        # )

        for key in obj.__dict__:
            if key[0] == '_' or getattr(obj, key) is None:
                continue
            attr = getattr(obj, key)
            if not isinstance(attr, list):
                setattr(obj_update, key, attr)

        await session.commit()
        return obj_update

    @staticmethod
    @AsyncDatabase.database_session
    async def delete(obj: any,
                     class_name: Table | Type,
                     *, session: AsyncSession
                     ) -> int:  # return deleted id
        if obj.id is None or obj.id == 0:
            return 0
        obj = await session.get(class_name, obj.id)
        # obj = await session.scalar(
        #     select(class_name).filter_by(id=obj.id)
        # )
        await session.delete(obj)
        await session.commit()
        return obj.id

    @staticmethod
    @AsyncDatabase.database_session
    async def delete_all(objs: list,
                         class_name: Table | Type,
                         *, session: AsyncSession
                         ) -> int:  # return deleted count
        count, async_tasks = 0, []
        for obj in objs:
            async_tasks.append(BaseDao.select(obj, class_name))
        res_group = await asyncio.gather(*async_tasks)
        '''
        NOTICE:
        asyncio.gather will ONLY add the exact ASYNC functions
        to the event loop, which means other things like:
        SYNC functions and awaited functions invoked in parameter list,
        will NOT be run concurrently. See async_test.py file
        '''
        async_tasks.clear()
        for res in res_group:  # each res is a list of object
            for obj in res:
                count += 1
                async_tasks.append(session.delete(obj))
        await asyncio.gather(*async_tasks)
        await session.commit()
        return count
