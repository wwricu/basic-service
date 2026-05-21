import time

import jieba
import pytest

from wwricu.database import post_db


@pytest.mark.asyncio
async def test_post_search():
    jieba.initialize()
    b = time.time()
    kw = 'Test'
    result = await post_db.search(kw)
    count = await post_db.search_count(kw)
    print([res.title for res in result])
    print(count)
    print(time.time() - b)
