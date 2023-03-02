import asyncio

from config import Config, MailConfig
from service import MailService


Config.mail = MailConfig(
    host="smtp.office365.com",
    port=587,
    username="iswangwr@outlook.com",
    password=""
)


async def test():
    await MailService.daily_mail()


if __name__ == '__main__':
    asyncio.run(test())
