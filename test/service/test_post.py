import time

import jieba
import pytest

from wwricu.service import post_service

@pytest.mark.asyncio
async def test_post_search():
    jieba.initialize()
    b = time.time()
    kw = 'Test'
    posts = await post_service.search(kw)
    if len(posts) == 0:
        print('no posts')
    for post in posts:
        print(post.id, post.title, '|', post.snippet)
    print(time.time() - b)
