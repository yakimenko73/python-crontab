import os
import signal

import time
import pause

import subprocess
import psutil

from crontab import CronTab
from croniter import croniter

from datetime import datetime


PATH_TO_CRONTAB = '/home/roman/Python-works/Simcord/Cron/mycron.tab'


def get_crontab(path):
	crontab = CronTab(tabfile=path)
	return crontab


def create_fork(crontab):
	for i in range(len(crontab)):
		pid = os.fork()
		id_job = i

		if pid == 0:
			break

	return pid, id_job


def work(id_job, path, crontab):
	flag = True
	while flag:
		time.sleep(2)

		crontab = get_crontab(path)
			
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


def main(path):
	crontab = get_crontab(path)

	pid, id_job = create_fork(crontab)

	print(pid, os.getpid())

	if pid == 0:
		work(id_job, path, crontab)
	else:
		os.wait()


if __name__ == "__main__":
	try:
		main(PATH_TO_CRONTAB)
	except KeyboardInterrupt:
		print('Interrupt')
		try:
			proc = psutil.Process(os.getpid())
			proc.kill()
		except SystemExit:
			os._exit(0)
