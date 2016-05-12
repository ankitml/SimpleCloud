import sys
import os
import subprocess
import logging
import time
import getpass
import shlex
import ConfigParser
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

def watch():
	logging.basicConfig(level=logging.INFO,
								format='%(asctime)s - %(message)s',
								datefmt='%Y-%m-%d %H:%M:%S')
	path = sys.argv[1] if len(sys.argv) > 1 else '.'
	event_handler = LoggingEventHandler()
	observer = Observer()
	observer.schedule(event_handler, path, recursive=True)
	observer.start()
	
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		observer.stop()
	observer.join()
	
def parse_config():
	global username, address, remote_root, local_root, stream_dirs, ssh_options, use_password
	
	config_path = os.path.abspath("../SimpleCloud.conf")
	config = ConfigParser.ConfigParser()
	config.read(config_path)
	
	username = config.get("Network", "user")
	address = config.get("Network", "address")
	stream_dirs = config.get("Directories",
		"stream_directories").split()
	remote_root = config.get("Directories", "remote_root")
	local_root = config.get("Directories", "local_root")
	ssh_options = config.get("Network", "ssh_options")
	if config.getboolean("Network", "password"):
		use_password = True
		ssh_options+=" -o password_stdin"
		

def mount():
	if use_password:
		password = getpass.getpass("Insert %s's password on %s: " %(username, address))
	
	for dir in stream_dirs:
		remote_dir = remote_root+dir
		local_dir = local_root+dir
		sshfs_args = shlex.split("sshfs "+username+"@"+address+":"+remote_dir+" "+local_dir+" "+ssh_options)
		print sshfs_args
		
		proc_echo = subprocess.Popen(["echo", password], stdout=subprocess.PIPE)
		proc_sshfs = subprocess.Popen(sshfs_args, stdin=proc_echo.stdout, stdout=subprocess.PIPE)
		proc_echo.wait()
		output = proc_sshfs.communicate()
		print output

def unmount():
	for dir in stream_dirs:
		print "Unmounting "+local_root+dir
		proc_unmount = subprocess.Popen(["fusermount","-uz", local_root+dir])

global username, address, remote_root, local_root, stream_dirs, ssh_options, use_password

#except KeyboardInterrupt:
#	unmount()
try:
	parse_config()
	mount()
	unmount()
except KeyboardInterrupt:
	unmount()
