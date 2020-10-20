import croniter
import datetime
import subprocess
import re


COMMAND_FOR_PARSING = "cat my_crontab.txt | sed '/ *#/d; /^ *$/d'"


def crontab_parsing():
	""" 
		Функция для получения списка команд с 
		файла etc/crontab
	"""
	list_jobs = []

	crontab = subprocess.check_output(COMMAND_FOR_PARSING, shell=True)
	crontab = bytes.decode(crontab, encoding='utf-8')

	list_jobs = re.split(r"^\s+|\n|\r|\s+$", crontab)

	return list_jobs


print(crontab_parsing())

now = datetime.datetime.now()

print(now)

cron = croniter.croniter('*/2 * *  * *', now)
print(cron.get_next(datetime.datetime))