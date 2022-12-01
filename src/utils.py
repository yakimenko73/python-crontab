import sys

from crontab import CronTab
from loguru import logger


def parse_crontab(path: str) -> CronTab:
    crontab_ = CronTab(tabfile=path)

    if not len(crontab_):
        logger.error(f'Not found cron jobs in {path} file')
        sys.exit(0)

    logger.info(f'{len(crontab_)} jobs parsed successfully')

    return crontab_
