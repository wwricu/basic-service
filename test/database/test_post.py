import pytest

from wwricu.database import post_db


@pytest.mark.asyncio
async def test_post_search():
    result = await post_db.search("Test")
    print([res.title for res in result])
    print([res.id for res in result])
