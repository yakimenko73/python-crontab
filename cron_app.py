from crontab import CronTab
from croniter import croniter

from datetime import datetime
import time
import pause
import subprocess


def get_list_jobs(crontab):
	list_jobs = []
	for job in crontab:
		list_jobs.append(job)
	return list_jobs


if __name__ == "__main__":
	PATH_TO_CRONTAB = '/home/roman/Python-works/Simcord/Cron/mycron.tab'

	crontab = CronTab(tabfile=PATH_TO_CRONTAB)

	flag = True

	print(get_list_jobs(crontab))

	while flag:
		t = datetime.today()
		base = datetime(t.year, t.month, t.day, t.hour, t.minute, t.second)

		iter_ = croniter(str(get_list_jobs(crontab)[0].slices), 
							base)
		task = iter_.get_next(datetime)

		print(str(task), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

		pause.until(task)

		print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Complete')

		flag = True