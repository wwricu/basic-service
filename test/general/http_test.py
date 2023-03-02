import asyncio
import aiohttp


async def get_image(url: str) -> bytes | None:
    async with aiohttp.ClientSession() as client:
        async with client.get(url) as response:
            if response.status != 200:
                return None
            image = await response.content.read()
            print(len(image))


if __name__ == '__main__':
    img_url = "https://thisiswwr.com/api/static/content/6/5cd9d735659ec617d4748db2d759456d.jpg"
    asyncio.run(get_image(img_url))
    res = {'test': "test"}
    print(res.update({'aaa': "test"}))
