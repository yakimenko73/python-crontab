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


def is_process_already_started(pid):
	if not pid: 
		return False

	try:
		os.kill(pid, 0)
		return True
	except OSError:
		return False


def get_pid_from_file(pidfile):
	pid = None
	if os.path.isfile(pidfile):
		logging.info("Is there a file with a pid? - True")
		with open(pidfile, "r") as f:
			try:
				pid = int(f.read())
				logging.info("The file is not empty? - True")
			except ValueError as ex:
				logging.warning(f"Exception: {ex}")
	else:
		logging.info("Is there a file with a pid? - False")

	return pid


def get_crontab(path):
	crontab = CronTab(tabfile=path)
	count_jobs = len(crontab)

	if count_jobs:
		return crontab, count_jobs

	logging.warning("The crontab file has no jobs. Exiting the programm")
	logging.info('Exit.' + f' PID: {os.getpid()}')

	os._exit(0)


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
	while True:
		date = get_current_date()
		try:
			iter_ = croniter(str(crontab[id_job].slices), date)
		except Exception as ex:
			# на случай попадания @yearly, @reboot и т.д.
			logging.info(f"Special job found. Task: {id_job} PID: {pid}")
			job = ' '.join([str(i) for i in crontab[id_job]])

			try:
				iter_ = croniter(job, date)
			except Exception as ex:
				logging.error(f"Unexpected error while setting job runtime. Task: {id_job} PID: {pid}")

		next_runtime = iter_.get_next(datetime)

		pause.until(next_runtime)

		status = os.system(str(crontab[id_job].command))
		logging.info(f'Task: {id_job}' + ' completed.' + f' PID: {pid}')


def start(path):
	logging.info(f'Parsing a crontab')
	crontab, count_jobs = get_crontab(path)
	logging.info(f'Crontab read successfully. Count jobs: {count_jobs}')

	pid, id_job = create_fork(crontab, count_jobs)
	print(pid)

	if pid == fork_pid:
		logging.info(f'Forked. PID: {os.getpid()}')
		workflow(id_job, crontab)
	else:
		os.wait()


def init():
	global regex_filepath, pidfile, fork_pid
	regex_filepath = re.compile("\w+/")
	pidfile = "temp/server.pid"
	fork_pid = 0

	true_log_levels = ['CRITICAL', 
		'ERROR', 
		'WARNING', 
		'INFO', 
		'DEBUG', 
	]

	true_file_modes = [
		'r',
		'w',
		'x',
		'a',
		'b',
		't',
		'+',
	]

	return true_log_levels, true_file_modes


def setup():
	global config
	config = configparser.ConfigParser()
	config.read("settings/settings.ini")

	log_setup()

	pid = get_pid_from_file(pidfile)

	if is_process_already_started(pid):
		logging.info("Is the script already running? - True")
		os._exit(0)
	else:
		pid = os.getpid()

	logging.info("Is the script already running? - False")

	pidfile_setup(pid)


def log_setup():
	log_level = config["LoggingSettings"]["LEVEL"].upper()
	file_mode = config["LoggingSettings"]["FILEMODE"].lower()
	file_name = config["Path"]["PATH_TO_LOG"]

	if not log_level in true_log_levels:
		log_level = 'DEBUG'

	if not file_mode in true_file_modes:
		file_mode = 'a'

	while True:
		try:
			logging.basicConfig(filename=file_name, 
				filemode=file_mode, 
				level=log_level,
				format='%(asctime)s.%(msecs)03d %(name)s %(levelname)s: %(message)s',
				datefmt='%Y-%m-%d %H:%M:%S')
			break
		except FileNotFoundError:
			pathdir = regex_filepath.findall(file_name)
			os.mkdir(''.join(pathdir))
			continue


def pidfile_setup(pid):
	while True:
		try:
			with open(pidfile, "w") as f:
				f.write(str(pid))
			break
		except FileNotFoundError:
			pathdir = regex_filepath.findall(pidfile)
			os.mkdir(''.join(pathdir))
			continue


if __name__ == "__main__":
	true_log_levels, true_file_modes = init()
	setup()

	try:
		logging.info('Beginning of work')
		start(config["Path"]["PATH_TO_CRONTAB"])
	except KeyboardInterrupt:
		logging.warning('KeyboardInterrupt' + f' PID: {os.getpid()}')
		os._exit(0)