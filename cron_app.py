import os
import sys

import logging
import configparser

import time
import pause

import psutil
import re

from crontab import CronTab
from croniter import croniter

from datetime import datetime


PIDFILE = "temp/server.pid"

FORK_PID = 0

TRUE_LOG_LEVELS = ['CRITICAL', 
	'ERROR', 
	'WARNING', 
	'INFO', 
	'DEBUG', 
]

TRUE_FILE_MODES = [
	'r',
	'w',
	'x',
	'a',
	'b',
	't',
	'+',
]


def is_process_already_started(pid: int):
	try:
		os.kill(pid, 0)
		return True
	except OSError:
		return False


def is_file(file):
	return True if os.path.isfile(file) else False


def get_pid_from_file():
	if is_file(PIDFILE):
		logging.info("Pid file exists")
		with open(PIDFILE, "r") as f:
			try:
				logging.info("The file is not empty")
				pid = int(f.read())
			except ValueError as ex:
				logging.warning("Invalid pid in file")
				pid = None
	else:
		logging.info("Pid file is not exists")
		pid = None

	return pid


def get_crontab(path):
	crontab = CronTab(tabfile=path)

	return crontab


def validation_crontab(crontab):
	count_jobs = len(crontab)
	if not count_jobs:
		logging.warning("The crontab file has no jobs. Exiting the programm")
		logging.info('Exit.' + f' PID: {os.getpid()}')

		os.unlink(PIDFILE)
		os._exit(0)

	return count_jobs


def get_current_date():
	t = datetime.today()
	date = datetime(t.year, 
		t.month, 
		t.day, 
		t.hour, 
		t.minute, 
		t.second)
	return date


def create_fork(crontab, count_jobs):
	for i in range(count_jobs):
		pid = os.fork()
		id_job = i

		if pid == 0:
			break
	return pid, id_job


def workflow(id_job, crontab):
	pid = os.getpid()
	logging.info(f'Forked. PID: {pid}')

	while True:
		date = get_current_date()
		try:
			job_runtime = str(crontab[id_job].slices)
			iter_ = croniter(job_runtime, date)
		except Exception as ex:
			# in case of hit @yearly, @reboot etc.
			logging.info(f"Special job found. Task: {id_job} PID: {pid}")
			job_runtime = ' '.join([str(time_unit) for time_unit in crontab[id_job]]) # like this is expected: */2 * * * *

			try:
				iter_ = croniter(job_runtime, date)
			except Exception as ex:
				# if an exception was raised 
				# what I did not expect
				logging.error(f"Unexpected error while setting job runtime. Task: {id_job} PID: {pid} Error: {ex}")

		next_job_runtime = iter_.get_next(datetime)

		pause.until(next_job_runtime)

		status = os.system(str(crontab[id_job].command))
		logging.info(f'Task: {id_job}' + ' completed.' + f' PID: {pid}')


def run(path):
	logging.info(f'Parsing a crontab')
	crontab = get_crontab(path)
	count_jobs = validation_crontab(crontab)
	logging.info(f'Crontab read successfully. Count jobs: {count_jobs}')

	pid, id_job = create_fork(crontab, count_jobs)

	if pid == FORK_PID:
		workflow(id_job, crontab)
	else:
		os.wait()


def init():
	global regex_filepath, path_to_crontab, path_to_log, log_filemode, log_level, config

	regex_filepath = re.compile("\w+/")

	config = None

	path_to_crontab = None
	path_to_log = None

	log_level = None
	log_filemode = None


def setup():
	config_setup()
	logging_setup()

	pid = get_pid_from_file()

	if pid:
		if is_process_already_started(pid):
			logging.info("The script is already running. Exit")
			os._exit(0)

	logging.info("Invalid pid in file or file is missing. Continue to work")

	pid = os.getpid()
	
	pidfile_setup(pid)


def config_setup():
	global path_to_crontab, path_to_log, log_filemode, log_level, config

	config = configparser.ConfigParser()
	config.read("settings/settings.ini")

	try:
		path_to_crontab = config["Path"]["PATH_TO_CRONTAB"]
		path_to_log = config["Path"]["PATH_TO_LOG"]

		log_level = config["LoggingSettings"]["LEVEL"].upper()
		log_filemode = config["LoggingSettings"]["FILEMODE"].lower()
	except KeyError as ex:
		logging.error("Incorrect parameters in the configuration file")


def logging_setup():
	global regex_filepath, path_to_log, log_filemode, log_level

	if not log_level in TRUE_LOG_LEVELS:
		log_level = 'DEBUG'

	if not log_filemode in TRUE_FILE_MODES:
		log_filemode = 'a'

	pathdir = ''.join(regex_filepath.findall(path_to_log))
	if pathdir:
		if not os.path.exists(pathdir):
			os.makedirs(pathdir)

	logging.basicConfig(filename=path_to_log, 
		level=log_level,
		filemode=log_filemode, 
		format='%(asctime)s.%(msecs)03d %(name)s %(levelname)s: %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S')


def pidfile_setup(pid: int):
	global regex_filepath

	pathdir = ''.join(regex_filepath.findall(PIDFILE))
	if pathdir:
		if not os.path.exists(pathdir):
			os.makedirs(pathdir)

	with open(PIDFILE, "w") as f:
		f.write(str(pid))


if __name__ == "__main__":
	init()
	setup()

	try:
		logging.info('Beginning of work')
		run(path_to_crontab)
	except KeyboardInterrupt:
		logging.warning('KeyboardInterrupt' + f' PID: {os.getpid()}')
		try:
			os.unlink(PIDFILE)
		except FileNotFoundError:
			pass
		os._exit(0)
