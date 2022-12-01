import os
import time
from datetime import datetime as dt

from crontab import CronTab, CronItem
from loguru import logger


class Cron:
    def __init__(self, crontab: CronTab):
        self._crontab = crontab

    def schedule(self) -> None:
        for job in self._crontab:
            pid = os.fork()
            if pid == 0:
                logger.info(f'Create child process {os.getpid()} for [{job.command}] job')

                self._run_job(job)

    @staticmethod
    def _run_job(job: CronItem) -> None:
        while True:
            res = job.run_pending(dt.now())
            if res != -1:
                logger.info(res)

            time.sleep(1)
