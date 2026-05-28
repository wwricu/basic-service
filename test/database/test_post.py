import time

import pytest

from wwricu.component.database import database_manager
from wwricu.database import post_db


@pytest.mark.asyncio
async def test_post_search():
    b = time.time()
    kw = 'Test'
    posts = await post_db.search(kw)
    count = await post_db.search_count(kw)
    for post in posts:
        print(post.id, post.title, '|', post.snippet)
    print(count)
    print(time.time() - b)


@pytest.mark.asyncio
async def test_database_vacuum():
    b = time.time()
    async with database_manager.engine.connect() as conn, conn.begin():
        await conn.exec_driver_sql('VACUUM')
    print(time.time() - b)
