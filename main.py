from importlib import *
from functions import *
from constants import *


def workflow(id_job, crontab):
	pid = os.getpid()
	logging.info(f'Forked. PID: {pid}')

	while True:
		date = get_current_date()
		try:
			job_runtime = str(crontab[id_job].slices)
			iter_ = croniter(job_runtime, date)
		except Exception as ex:
			# in case of hit @yearly, @reboot и т.д.
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