import aiohttp
import asyncio


async def test():
    client = aiohttp.ClientSession()
    async with client.get(
        'http://t.weather.itboy.net/api/weather/city/101020100'
    ) as response:
        print(response.status)
        print(await response.json())
    await client.close()

if __name__ == '__main__':
    asyncio.run(test())
