import time

import pytest

from wwricu.component.tokenize import build_match
from wwricu.database import post_db


@pytest.mark.asyncio
async def test_post_search():
    b = time.time()
    posts = await post_db.search(build_match('Test'))
    for post in posts:
        print(post.id, post.title)
    print(time.time() - b)
