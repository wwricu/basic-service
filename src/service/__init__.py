from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .algolia_service import AlgoliaService
from .http_service import HTTPService
from .mail_service import MailService
from .render_service import RenderService
from .resource_service import ResourceService
from .security_service import APIThrottle, RoleRequired, SecurityService
from .sql_admin import SqlAdmin
from .tag_service import TagService
from .user_service import UserService
from config import logger


def schedule_jobs():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        MailService.daily_mail,
        CronTrigger(hour=8, timezone='Asia/Shanghai')
    )
    scheduler.add_job(
        HTTPService.parse_bing_image_url,
        CronTrigger(hour=1, timezone='US/Pacific')
    )
    scheduler.start()
    logger.info('schedule jobs started')


__all__ = [
    'APIThrottle',
    'AlgoliaService',
    'HTTPService',
    'MailService',
    'RenderService',
    'ResourceService',
    'RoleRequired',
    'schedule_jobs',
    'SecurityService',
    'SqlAdmin',
    'TagService',
    'UserService'
]
