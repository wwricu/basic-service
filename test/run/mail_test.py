import asyncio
from email.mime.text import MIMEText
from smtplib import SMTP

from src.config import Config, MailConfig
from src.service import MailService


Config.mail = MailConfig(
    host="smtp.office365.com",
    port=587,
    username="iswangwr@outlook.com",
    password="wfavardsuprrsdvl"
)


async def test():
    await MailService.daily_mail()


if __name__ == '__main__':
    asyncio.run(test())
