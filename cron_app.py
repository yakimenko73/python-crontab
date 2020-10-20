import os

from crontab import CronTab
from croniter import croniter

from datetime import datetime
import time
import pause
import subprocess
import psutil
import signal

def get_crontab(path):
	crontab = CronTab(tabfile=PATH_TO_CRONTAB)
	return crontab


class GracefulKiller:
	kill_now = False
	def __init__(self):
		signal.signal(signal.SIGINT, self.exit_gracefully)
		signal.signal(signal.SIGTERM, self.exit_gracefully)

	def exit_gracefully(self,signum, frame):
		self.kill_now = True

if __name__ == "__main__":
	PATH_TO_CRONTAB = '/home/roman/Python-works/Simcord/Cron/mycron.tab'

	crontab = get_crontab(PATH_TO_CRONTAB)

	flag = True

	for i in range(len(crontab)):
		pid = os.fork()
		id_job = i
		if pid == 0:
			break

	print(pid, os.getpid())

	if pid == 0:
		while flag:
			time.sleep(1)
			killer = GracefulKiller()

			crontab = get_crontab(PATH_TO_CRONTAB)
			
			t = datetime.today()
			base = datetime(t.year, 
							t.month, 
							t.day, 
							t.hour, 
							t.minute, 
							t.second)

			iter_ = croniter(str(crontab[id_job].slices),
									base)
			task = iter_.get_next(datetime)

			print(str(task), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id_job)

			pause.until(task)

			status = os.system(str(crontab[id_job].command))
			print(f'Task - {id_job}' + ' completed')

			if killer.kill_now:
				flag = False
			else:
				flag = True
