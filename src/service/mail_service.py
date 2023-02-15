import asyncio
import datetime
from email.mime.text import MIMEText
from smtplib import SMTP

from config import Config, logger
from schemas import WeatherSchema
from service.http_service import HTTPService


class MailService:
    @classmethod
    async def send_mail(
        cls,
        recipients: list[str],
        subject: str | None = None,
        message: str | None = None,
    ):
        if Config.mail is None:
            return

        msg = MIMEText(message, 'html', _charset='utf-8')
        msg['subject'] = subject

        smtp = SMTP(
            host=Config.mail.host,
            port=Config.mail.port
        )
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
            logger.warn('send mail failed', e)
        finally:
            smtp.close()

    @classmethod
    async def daily_mail(cls):
        try:
            weather = WeatherSchema.parse_obj(await HTTPService.get_weather())
            message = f"""
            <div
            style="font-size: 24px;
            font-family: Google Sans, Helvetica, sans-serif;"
            >
            <li>Weather in {weather.cityInfo.city}: {weather.data.forecast[0].type}</li>
            <li>Air quality: {weather.data.quality}</li>
            <li>
            Temperature: {weather.data.forecast[0].low} ~ {weather.data.forecast[0].high}
            </li>
            <li>Humidity is {weather.data.shidu}</li>
            </div>
            """
        except Exception as e:
            logger.warn('failed to get weather')
            message = e.__str__()
        asyncio.create_task(MailService.send_mail(
            ['iswangwr@outlook.com'],
            f'Today is {datetime.datetime.today().date()}',
            message,
        ))
