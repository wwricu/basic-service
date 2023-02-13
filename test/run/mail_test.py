import asyncio
from email.mime.text import MIMEText
from smtplib import SMTP


class MailService:
    @classmethod
    async def send_mail(
        cls,
        recipients: list[str],
        subject: str | None = None,
        message: str | None = None,
        *,
        sender_show: str | None = None,
        recipient_show: str | None = None,
        cc_show: str | None = None
    ):
        msg = MIMEText(message, 'plain', _charset='utf-8')
        msg['subject'] = subject
        msg['from'] = sender_show
        msg['to'] = recipient_show
        msg['cc'] = cc_show

        smtp = SMTP(
            host='smtp.office365.com',
            port=587
        )

        try:
            smtp.starttls()
            smtp.login(
                user='iswangwr@outlook.com',
                password=''
            )
            smtp.sendmail(
                from_addr='iswangwr@outlook.com',
                to_addrs=recipients,
                msg=msg.as_string()
            )
        except Exception as e:
            print(e)
        finally:
            smtp.close()


asyncio.run(MailService.send_mail(
    ['iswangwr@outlook.com'],
    'A another day begins...',
    'Thanks for your hard working.',
))
