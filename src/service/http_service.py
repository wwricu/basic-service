# coding=utf-8
import re

import aiohttp
from config import logger


class HTTPService:
    """
    city code on https://github.com/baichengzhou/weather.api/
    blob/master/src/main/resources/citycode-2019-08-23.json
    """
    WEATHER_URL: str = 'http://t.weather.itboy.net/api/weather/city/101020100'

    @classmethod
    async def get_weather(cls) -> dict | None:
        async with aiohttp.ClientSession() as client:
            async with client.get(cls.WEATHER_URL) as response:
                if response.status != 200:
                    return None
                return await response.json()

    @staticmethod
    async def get_image(url: str) -> bytes:
        # TODO: parse url parameters
        async with aiohttp.ClientSession() as client:
            async with client.get(url) as response:
                if response.status != 200:
                    raise FileNotFoundError
                return await response.read()

    BING_URL: str = 'https://www.bing.com'
    BING_IMAGE_PATTERN: str = r'(?<=href=")/th\?id=.+?\.jpg'

    @classmethod
    async def parse_bing_image_url(cls) -> str:
        async with aiohttp.ClientSession() as client:
            async with client.get(cls.BING_URL) as response:
                if response.status != 200:
                    raise FileNotFoundError
                return '{bing_url}{image_path}'.format(
                    bing_url=cls.BING_URL,
                    image_path=re.search(
                        cls.BING_IMAGE_PATTERN,
                        (await response.read()).decode(
                            encoding=response.get_encoding()
                        )
                    ).group()
                )
