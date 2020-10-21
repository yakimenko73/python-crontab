import os
import logging

import time
import pause

import psutil

from crontab import CronTab
from croniter import croniter

from datetime import datetime


PATH_TO_CRONTAB = '/home/roman/Python-works/Simcord/Cron/mycron.tab'
PATH_TO_LOG = '/home/roman/Python-works/Simcord/Cron/mainlog.log'

logging.basicConfig(filename=PATH_TO_LOG, filemode='a', level=logging.DEBUG,
					format='%(asctime)s.%(msecs)03d %(name)s %(levelname)s: %(message)s',
					datefmt='%Y-%m-%d %H:%M:%S')


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
		t = datetime.today()
		base = datetime(t.year, 
							t.month, 
							t.day, 
							t.hour, 
							t.minute, 
							t.second)

		try:
			iter_ = croniter(str(crontab[id_job].slices),
									base)
		except Exception:
			# на случай попадания @yearly, @reboot etc.
			logging.warning('Specific job')
			job = ''
			for i in crontab[3]:
				job += str(i) + ' '
			iter_ = croniter(job, base)

		task = iter_.get_next(datetime)

		pause.until(task)

		status = os.system(str(crontab[id_job].command))
		logging.info(f'Task: {id_job}' + ' completed' + f' PID: {os.getpid()}')


def main(path):
	logging.info('Programm start')
	crontab = get_crontab(path)
	logging.info('Parsing a crontab')

	pid, id_job = create_fork(crontab)

	if pid == 0:
		logging.info('Forked')
		work(id_job, path, crontab)
	else:
		os.wait()


if __name__ == "__main__":
	try:
		main(PATH_TO_CRONTAB)
	except KeyboardInterrupt:
		logging.warning('KeyboardInterrupt')
		try:
			proc = psutil.Process(os.getpid())
			proc.kill()
		except SystemExit:
			logging.warning('SystemExit')
			os._exit(0)
