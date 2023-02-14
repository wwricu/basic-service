from email.mime.text import MIMEText
from smtplib import SMTP

from config import Config, logger


class MailService:
    @classmethod
    async def send_mail(
        cls,
        recipients: list[str],
        subject: str | None = None,
        message: str | None = None,
    ):
        msg = MIMEText(message, 'plain', _charset='utf-8')
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
        await cls.send_mail(
            ['iswangwr@outlook.com'],
            'Another day begins...',
            '<p>Thanks for your hard working.</p>',
        )
