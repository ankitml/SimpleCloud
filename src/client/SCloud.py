
# General tools
import os
import logging
import time

#
import getpass
#import shlex



# Multi-threading tools
import Queue

#Python 3
#import configparser
#Python 2

from src.common import ConfigurationParser
import SSHFSmounter
import src.common.Observer as Observer
from FileSynchronizer import FileSynchronizer

def get_config():
	global parameters
	parameters = ConfigurationParser.parse_config()
	print "Parameters: "
	print parameters

def watch():
	global observer
	synchronizer_threads = len(parameters["sync_dirs"])
	if "sync_threads" in parameters: 
		synchronizer_threads = parameters["sync_threads"]
	print "Synchronizer threads: " + str(synchronizer_threads)

	synchronizers = []
	
	for i in range (synchronizer_threads):
		print "Starting thread "+str(i)
		synchronizer = FileSynchronizer(i, tasks)
		synchronizer.start()
		synchronizers.append(synchronizer)

	observer = Observer.getObserver(parameters["sync_dirs"], tasks)
	observer.start()
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print "Stopping observer"
		observer.stop()
	observer.join()
	print "Stopping queue"
	tasks.join()
	print "Stopping synchronizers"
	for synchronizer in synchronizers:
		print "Stopping thread "+str(synchronizer.thread_id)
		synchronizer.observe=False
		synchronizer.join(timeout=0.5)
	print "Here"
	
	# for sync in parameters["sync_dirs"]:
	# 	local = sync["local"]
	# 	mountpoint = sync["mountpoint"]
	#
	# 	handler1 = FileSystemEventHandler(local, mountpoint, tasks)
	# 	observer.schedule(handler1, local, recursive=True)
	#
	# 	#handler2 = FileSystemEventHandler(mountpoint, local, tasks)
	# 	#observer.schedule(handler2, mountpoint, recursive=True)
		
	# observer.start()
	#
	# try:
	# 	while True:
	# 		time.sleep(1)
	# except KeyboardInterrupt:
	# 	observer.stop()
	# 	observer.join()
	# 	for synchronizer in synchronizers:
	# 		synchronizer.join()
	# 	while not tasks.empty():
	# 		task = tasks.get(block=True)
	# 		print task

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
		print error
		unmount()
		exit(1)

def self_mount():
	proc_echo = None
	
	if use_password:
		password = getpass.getpass("Insert %s's password on %s: " %(username, address))
		proc_echo = subprocess.Popen(["echo", password], stdout=subprocess.PIPE)
	
	for dir in parameters["stream_dirs"]:
		print "This stream dir: "+dir
		remote_dir = remote_root+dir
		local_dir = local_root+dir
		sshfs_args = shlex.split("sshfs "+username+"@"+address+":"+
			remote_dir+" "+local_dir+" "+ssh_options)
		print(sshfs_args)
		if use_password:
			pass
			#proc_sshfs = subprocess.Popen(sshfs_args, stdin=proc_echo.stdout, stdout=subprocess.PIPE)
			#proc_echo.wait()
			#output = proc_sshfs.communicate()
			#print(output)
		else:
			proc_sshfs = subprocess.call(sshfs_args)
			output = proc_sshfs.communicate()
			print(output)

def unmount():
	#sync_path = 
	for dir in parameters["stream_dirs"]+parameters["sync_dirs"]:
		try:
			SSHFSmounter.unmount(dir["mountpoint"])
		except SSHFSmounter.UnmountingError as error:
			print error
	#for dir in parameters["sync_dirs"]:
	#	SSHFSmounter.unmount(dir["mountpoint"])
	

global parameters, observer
tasks = Queue.Queue()

get_config()
watch()
exit()