import asyncio
from typing import Awaitable

import aiohttp
from algoliasearch.search_client import SearchClient


app_id = ''
api_key = ''
search_key = ''  # search key
index_name = 'blog_content_index'


async def delete_non_exist():
    async with SearchClient.create(app_id, api_key) as client:
        index = client.init_index('dev_blog_post')

        results = await index.delete_object_async(2222)
        while isinstance(results, Awaitable):
            results = await results
        print(results)


async def restful_search(keyword: str):
    url = f'https://{app_id}-dsn.algolia.net/1/indexes/{index_name}/query'
    headers = {
        'X-Algolia-Application-Id': app_id,
        'X-Algolia-API-Key': search_key,
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {"params": 'query=log'}
    async with aiohttp.ClientSession() as client:
        async with client.post(
            url=url,
            headers=headers,
            json=data,
        ) as response:
            if response.status != 200:
                print('failed')
            print(await response.json())


async def save_object():
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


async def main():
    await restful_search('l')

asyncio.run(main())
