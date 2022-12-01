import os
import signal
from typing import Final

import utils
from config import Config
from cron import Cron

CONFIG_PATH: Final[str] = '../config/config.yaml'

if __name__ == '__main__':
    cfg: Config = Config.load(CONFIG_PATH)
    cfg.configure_logger()

    crontab = utils.parse_crontab(cfg.app.crontab_path)
    cron = Cron(crontab)

    try:
        cron.schedule()
        os.wait()
    except KeyboardInterrupt as ex:
        os.killpg(os.getpgid(os.getpid()), signal.SIGCHLD)
