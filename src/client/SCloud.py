
# General tools
import os
import logging
import time

#
import getpass
#import shlex

# Multi-threading tools
from queue import Queue

#Python 3
#import configparser
#Python 2
from . import SSHFSmounter
from .FileSynchronizer import FileSynchronizer
from .TaskReceiver import TaskReceiver
from common import ConfigurationParser, Observer

def get_config():
	global parameters, tasks
	parameters = ConfigurationParser.parse_config()
	tasks = Queue()
	print("Parameters: " + str(parameters))

def connect():
	global receiver, tasks
	host = parameters["host"]
	port = parameters["port"]
	receiver = TaskReceiver(host, port, tasks, parameters["sync_dirs"])

	receiver.start()
	time.sleep(1)

def watch():
	global observer
	synchronizer_threads = len(parameters["sync_dirs"])
	if "sync_threads" in parameters: 
		synchronizer_threads = parameters["sync_threads"]
	print("Synchronizer threads: " + str(synchronizer_threads))

	synchronizers = []
	
	for i in range (synchronizer_threads):
		print("Starting thread " + str(i))
		synchronizer = FileSynchronizer(i, tasks)
		synchronizer.start()
		synchronizers.append(synchronizer)

	receiver.watch_socket.set()

	observer = Observer.getObserver(parameters["sync_dirs"], tasks)
	observer.start()
	try:
		while True:
			if not receiver.is_alive():
				raise(ConnectionRefusedError)
			time.sleep(1)
	except (KeyboardInterrupt, ConnectionRefusedError):
		print("Stopping observer")
		observer.stop()
	observer.join()
	print("Stopping task receiver")
	#receiver.watch_socket.clear()
	receiver.join()
	print("Stopping queue")
	tasks.join()
	print("Stopping synchronizers")
	for synchronizer in synchronizers:
		print("Stopping thread " + str(synchronizer.thread_id))
		synchronizer.keep_running=False
		synchronizer.join(timeout=1)
	print("Here")

def mount():
	host = parameters["host"]
	user = parameters["user"]
	ssh_options = parameters["ssh_options"]
	try:
		for dir in parameters["stream_dirs"]:
			SSHFSmounter.mount(host, dir["path"], dir["mountpoint"], 
				user=user, ssh_options=ssh_options)
		for dir in parameters["sync_dirs"]:
			SSHFSmounter.mount(host, dir["path"], dir["mountpoint"], 
				user=user, ssh_options=ssh_options)
	except SSHFSmounter.MountingError as error:
		print(error)
		unmount()
		exit(1)

def unmount():
	#sync_path = 
	for dir in parameters["stream_dirs"]+parameters["sync_dirs"]:
		try:
			SSHFSmounter.unmount(dir["mountpoint"])
		except SSHFSmounter.UnmountingError as error:
			print(error)
	#for dir in parameters["sync_dirs"]:
	#	SSHFSmounter.unmount(dir["mountpoint"])

global parameters, observer, receiver, tasks

#1 - get config
#2 - create task queue
#3 - connect to server
#4 - observe
get_config()
if parameters["sync_dirs"]:
	connect()
	watch()

exit()