import os
import sys

import logging
import configparser

import time
import pause

import psutil

from crontab import CronTab
from croniter import croniter

from datetime import datetime


config = configparser.ConfigParser()
config.read("settings/settings.ini")

pidfile = "temp/server.pid"

logging.basicConfig(filename = config["Path"]["PATH_TO_LOG"], 
					filemode='a', 
					level=logging.DEBUG,
					format = '%(asctime)s.%(msecs)03d %(name)s %(levelname)s: %(message)s',
					datefmt = '%Y-%m-%d %H:%M:%S')


def is_process_started(pid):
	""" Проверка запущен ли этот скрипт """
	try:
		os.kill(pid, 0)
		return True
	except OSError:
		return False


def check_pid():
	""" Проверка является ли pid запущенного скрипта уже активным процессом """
	if os.path.isfile(pidfile):
		logging.info("Is there a file with a pid? - True")
		with open(pidfile, "r") as f:
			# случай, если файл server.pid пустой
			try:
				pid = int(f.read())
				logging.info("The file is not empty? - True")
			except ValueError as ex:
				logging.warning(f"Exception: {ex}")
				return

		if is_process_started(pid):
			logging.info("Is the script already running? - True")
			try:
				proc = psutil.Process(os.getpid())
				proc.kill()
			except SystemExit:
				logging.warning('SystemExit')
				os._exit(0)

		logging.info("Is the script already running? - False")


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
			iter_ = croniter(str(crontab[id_job].slices), base)
		except Exception:
			# на случай попадания @yearly, @reboot etc.
			logging.warning('Specific job')
			job = ''
			for i in crontab[3]:
				job += str(i) + ' '

			iter_ = croniter(job, base)

		task_time = iter_.get_next(datetime)

		pause.until(task_time)

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
	check_pid()

	# при каждом запуске скрипта будет записываться его pid,
	# это нужно для того чтобы исключить возможность добавить
	# этот же файл для исполнения в crontab
	pid = str(os.getpid())
	with open(pidfile, "w") as f:
		f.write(pid)

	try:
		main(config["Path"]["PATH_TO_CRONTAB"])
	except KeyboardInterrupt:
		logging.warning('KeyboardInterrupt' + f' PID: {os.getpid()}')
		try:
			proc = psutil.Process(os.getpid())
			proc.kill()
		except SystemExit:
			logging.warning('SystemExit')
			os._exit(0)
	finally:
		os.unlink(pidfile)