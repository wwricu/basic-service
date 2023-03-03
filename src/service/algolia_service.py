from __future__ import annotations
from typing import Awaitable

from algoliasearch.search_index_async import SearchClient

from config import Config
from dao import AsyncDatabase, BaseDao
from models import Content
from schemas import AlgoliaPostIndex


class AlgoliaService:
    @staticmethod
    async def save_contents(contents: list[AlgoliaPostIndex]):
        if Config.algolia is None:
            return
        async with SearchClient.create(
            Config.algolia.app_id,
            Config.algolia.admin_key
        ) as client:
            index = client.init_index(Config.algolia.index_name)
            # return algoliasearch.responses.IndexingResponse
            await index.save_objects_async([
               idx.dict() for idx in contents
            ])

    @staticmethod
    async def delete_contents(object_ids: list[int]):
        if Config.algolia is None:
            return
        async with SearchClient.create(
            Config.algolia.app_id,
            Config.algolia.admin_key
        ) as client:
            index = client.init_index(Config.algolia.index_name)
            await index.delete_objects_async(object_ids)

    @staticmethod
    async def search_content(keyword: str) -> dict:
        if Config.algolia is None:
            return dict()
        async with SearchClient.create(
            Config.algolia.app_id,
            Config.algolia.admin_key
        ) as client:
            index = client.init_index(Config.algolia.index_name)
            results: dict | Awaitable = await index.search_async(keyword)
            while isinstance(results, Awaitable):
                results = await results
            return results

    @staticmethod
    @AsyncDatabase.use_database
    async def refresh_all_contents() -> int:
        if Config.algolia is None:
            return 0
        contents = await BaseDao.select(Content(parent_url='/post'), Content)
        await AlgoliaService.save_contents(
            [AlgoliaPostIndex.parse_content(c) for c in contents]
        )
        return len(contents)
