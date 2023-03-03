import asyncio
from typing import Awaitable

from algoliasearch.search_client import SearchClient

app_id = ''
api_key = ''


async def delete_non_exist():
    async with SearchClient.create(app_id, api_key) as client:
        index = client.init_index('dev_blog_post')

        results = await index.delete_object_async(2222)
        while isinstance(results, Awaitable):
            results = await results
        print(results)


async def main():
    async with SearchClient.create(app_id, api_key) as client:
        index = client.init_index('dev_blog_post')

        await index.save_objects_async([
            {'objectID': 1, 'name': 'foo'},
            {'objectID': 2, 'name': 'bar'}
        ])

        results = await index.search_async('')
        while isinstance(results, Awaitable):
            results = await results
        print(results)

asyncio.run(delete_non_exist())
