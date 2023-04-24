import os
import sys
import requests

from os import path
from datetime import datetime, timedelta

from app import CONSTANTS

def refresh() -> str:
	"""
	Refreshes or Creates day's schedule
	1. Call Free
	2. Call Generate
	"""	
	today = datetime.now().replace(tzinfo=CONSTANTS.TZ).strftime("%d-%m-%Y %H:%M:%S")

	fr = free()
	if fr < 0:
		return f"{today} -> Couldn't delete file"
	
	ge = generate()
	if ge > 0:
		return f"{today} -> Sucessfully created logfile"
	
	return f"{today} -> Couldn't create logfile"


def free() -> int:
	"""
	Allows for new day schedule to be created
	"""
	today = datetime.now().replace(tzinfo=CONSTANTS.TZ).strftime("%A-%d-%m-%Y")
	if not path.isfile(f"./app/logs/{today}.json"):
		return 0

	try:
		os.remove(f"./app/logs/{today}.json")
		return 1
	except OSError:
		return -1

def generate() -> int:
	req = requests.post(
				f"{CONSTANTS.API_URL}/generate"
			)

	if req.status_code == 200:
		return 1

	return -1

def purge():
	files = [x for i,j,x in os.walk("./app/logs")][0]
	for logfile in files:
		if logfile.endswith(".json"):
			os.remove(f"./app/logs/{logfile}")
	return

def main():
	command_list = [
		"-f",
		"--free",
		"-r",
		"--refresh",
		"-g",
		"--generate",
		"-p",
		"--purge"
	]
	command = sys.argv[1].replace(' ', '')
	if not command or command not in command_list:
		print("[X] Usage:")
		print("\t python3/python/py refine.py <commmand>")
		print("\t Requires Python version 3.10+. Run python --version to check")
		print("[X] Available Commands")
		print("\t -f, --free, Allows for new day schedule to be created")
		print("\t -r, --refresh, Refreshes or Creates day's schedule")
		print("\t -g, --generate, Generates today's json log file")
		print("\t -p, --purge, Removes all log files")
		sys.exit(0)

	if command == "-f" or command == "--free":
		free()
	elif command == "-r" or  command == "--refresh":
		refresh()
	elif command == "-g" or command == "--generate":
		generate()
	elif command == "-p" or command == "--purge":
		accept = input("[x] Every log file will be deleted. Proceed? y | N\n")
		if accept.lower() == 'y':
			purge()
		else:
			print("[x] Purge Action Cancelled")

if __name__ == "__main__":
	main()