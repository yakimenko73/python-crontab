from importlib import *
from constants import *

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


def get_current_date():
	t = datetime.today()
	date = datetime(t.year, 
		t.month, 
		t.day, 
		t.hour, 
		t.minute, 
		t.second)
	return date


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


def create_fork(crontab, count_jobs):
	for i in range(count_jobs):
		pid = os.fork()
		id_job = i

		if pid == FORK_PID:
			break
	return pid, id_job