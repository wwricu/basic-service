import asyncio
from typing import Awaitable

from algoliasearch.search_client import SearchClient

app_id = ''
api_key = ''


async def main():
    async with SearchClient.create(app_id, api_key) as client:
        index = client.init_index('dev_blog_post')

        response = await index.save_objects_async([
            {'objectID': 1, 'name': 'foo'},
            {'objectID': 2, 'name': 'bar'}
        ])

        results = await index.search_async('')
        while isinstance(results, Awaitable):
            results = await results
        print(results)

asyncio.run(main())
