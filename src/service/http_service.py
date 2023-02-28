import aiohttp


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
        async with aiohttp.ClientSession() as client:
            async with client.get(url) as response:
                print('code!', response.status)
                if response.status != 200:
                    raise FileNotFoundError
                return await response.read()
