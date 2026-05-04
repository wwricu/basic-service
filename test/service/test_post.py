import pytest

from wwricu.database import post_db
from wwricu.service import post_service


@pytest.mark.asyncio
async def test_get_resource_keys():
    post = await post_db.find_by_id(7390764690)
    keys = await post_service.get_resource_keys(str(post.content))
    print(keys)
