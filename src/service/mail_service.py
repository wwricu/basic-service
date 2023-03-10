import asyncio
import datetime
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from smtplib import SMTP
from threading import Thread

import aiosmtplib

from .http_service import HTTPService
from .render_service import RenderService
from config import Config, logger
from schemas import WeatherSchema


class MailService:
    @classmethod
    def format_addr(cls, addr: str):
        name, addr = parseaddr(addr)
        return formataddr((name, addr))

    @classmethod
    async def send_mail_async(
        cls,
        recipients: list[str],
        subject: str | None = None,
        message: str | None = None
    ):
        if Config.mail is None:
            return

        msg = MIMEText(message, 'html', _charset='utf-8')
        try:
            msg['From'] = cls.format_addr(Config.mail.username)
            msg['To'] = cls.format_addr(recipients[0])
            msg['subject'] = subject
        except Exception as e:
            logger.error('failed compose email', e)

        smtp = aiosmtplib.SMTP(
            hostname=Config.mail.host,
            port=Config.mail.port,
            start_tls=False,
            use_tls=False
        )
        try:
            await smtp.connect()
            await smtp.starttls()
            await smtp.login(Config.mail.username, Config.mail.password)
            await smtp.send_message(recipients=recipients, message=msg)
        except aiosmtplib.SMTPException as e:
            logger.warn('failed to send mail', e)
        finally:
            smtp.close()

    @classmethod
    def send_mail(
        cls,
        recipients: list[str],
        subject: str | None = None,
        message: str | None = None
    ):
        if Config.mail is None:
            return
        msg = MIMEText(message, 'html', _charset='utf-8')
        try:
            msg['From'] = cls.format_addr(Config.mail.username)
            msg['To'] = cls.format_addr(recipients[0])
            msg['subject'] = subject
            msg['subject'] = subject
        except Exception as e:
            logger.error('failed compose email', e)

        smtp = SMTP(host=Config.mail.host, port=Config.mail.port)
        try:
            smtp.starttls()
            smtp.login(
                user=Config.mail.username,
                password=Config.mail.password
            )
            smtp.sendmail(
                from_addr=Config.mail.username,
                to_addrs=recipients,
                msg=msg.as_string()
            )
        except Exception as e:
            logger.warn('failed to send mail', e)
        finally:
            smtp.close()

    @classmethod
    def send_email_thread(cls, *args, **kwargs):
        thread = Thread(target=cls.send_mail, args=args, kwargs=kwargs)
        thread.start()

    @classmethod
    async def daily_mail(cls):
        try:
            weather = WeatherSchema.parse_obj(await HTTPService.get_weather())
            message = RenderService.daily_mail(weather)
        except Exception as e:
            logger.warn('failed to render or get weather')
            message = e.__str__()
        asyncio.create_task(MailService.send_mail_async(
            ['iswangwr@outlook.com'],
            f'Today is {datetime.datetime.today().date()}',
            message
        ))
