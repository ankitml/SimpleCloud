
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

#from watchdog.observers.read_directory_changes import WindowsApiObserver as Observer
import ConfigurationParser
import SSHFSmounter
from watchdog.observers import Observer
from EventHandler import FileSystemEventHandler
from FileSynchronizer import FileSynchronizer

def get_config():
	global parameters
	parameters = ConfigurationParser.parseconfig()

def watch(synchronizer_threads):
	localpath = "/home/francisco/temp/a"
	remotepath = "/home/francisco/temp/b"
	
	synchronizers = []
	
	for i in range (synchronizer_threads):
		synchronizer = FileSynchronizer(i, tasks)
		synchronizer.start()
		synchronizers.append(synchronizer)
	
	paths = [ (localpath, remotepath) ]
	observer = Observer()
	
	for path in paths:
		logging.basicConfig(level=logging.INFO,
									format='%(asctime)s - %(message)s',
									datefmtFileSystemEventHandler='%Y-%m-%d %H:%M:%S')
		
		handler1 = FileSystemEventHandler(localpath, remotepath, tasks)
		observer.schedule(handler1, path[0], recursive=True)
		
		handler2 = FileSystemEventHandler(remotepath, localpath, tasks)
		observer.schedule(handler2, path[1], recursive=True)
		
	observer.start()
	
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		observer.stop()
		observer.join()
		for synchronizer in synchronizers:
			synchronizer.join()
		#while not tasks.empty():
		#	task = tasks.get(block=True)
		#	print task

def mount():
	for dir in stream_dirs:
		SSHFSmounter.mount(host, dir["path"], dir["mountpoint"], 
			user=username, ssh_options=ssh_options)
	while True:
		time.sleep(1)

def self_mount():
	proc_echo = None
	
	if use_password:
		password = getpass.getpass("Insert %s's password on %s: " %(username, address))
		proc_echo = subprocess.Popen(["echo", password], stdout=subprocess.PIPE)
	
	for dir in stream_dirs:
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
	for dir in stream_dirs:
		SSHFSmounter.unmount(dir["mountpoint"])

global parameters
tasks = Queue.Queue()

try:
	get_config()
	#mount()
	#unmount()
	watch()
except KeyboardInterrupt:
	unmount()
