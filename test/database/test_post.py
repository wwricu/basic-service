import time

import pytest

from wwricu.database import post_db


@pytest.mark.asyncio
async def test_post_search():
    b = time.time()
    kw = 'Test'
    posts = await post_db.search(kw)
    for post in posts:
        print(post.id, post.title, '|', post.snippet)
    print(time.time() - b)
