import sys
import os
import subprocess
import logging
import time
import getpass
import shlex

#Python 3
#import configparser
#Python 2
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

def get_parameter_generic(config_path, config, section, option):
	if not config.has_option(section, option):
		#Python 3
		#configuration = input(option + ": ")
		#Python 2
		configuration = raw_input(option + ": ")

		config.set(section, option, configuration)
		with open(config_path, "w") as configfile:
			config.write(configfile)

def get_parameter(config_path, config, section, option):
	get_parameter_generic(config_path, config, section, option)
	return config.get(section, option)

def get_parameter_boolean(config_path, config, section, option):
	get_parameter_generic(config_path, config, section, option)
	return config.getboolean(section, option)

def parse_config():
	global username, address, remote_root, local_root, stream_dirs, ssh_options, use_password

	config_path = os.path.abspath("../SimpleCloud.conf")

	#Python 3
	#config = configparser.ConfigParser()
	#Python 2
	config = ConfigParser.ConfigParser()

	config.read(config_path)

	username = 		get_parameter(config_path, config, "Network", "user")
	address = 		get_parameter(config_path, config, "Network", "address")
	stream_dirs = 	get_parameter(config_path, config, "Directories",
		"stream_directories").split()
	remote_root = 	get_parameter(config_path, config, "Directories", "remote_root")
	local_root = 	get_parameter(config_path, config, "Directories", "local_root")
	ssh_options = 	get_parameter(config_path, config, "Network", "ssh_options")
	use_password =	get_parameter_boolean(config_path, config, "Network", "password")
	if use_password:
		ssh_options+=" -o password_stdin"
	exit()

def mount():
	if use_password:
		password = getpass.getpass("Insert %s's password on %s: " %(username, address))
	
	for dir in stream_dirs:
		remote_dir = remote_root+dir
		local_dir = local_root+dir
		sshfs_args = shlex.split("sshfs "+username+"@"+address+":"+remote_dir+" "+local_dir+" "+ssh_options)
		print(sshfs_args)
		
		proc_echo = subprocess.Popen(["echo", password], stdout=subprocess.PIPE)
		proc_sshfs = subprocess.Popen(sshfs_args, stdin=proc_echo.stdout, stdout=subprocess.PIPE)
		proc_echo.wait()
		output = proc_sshfs.communicate()
		print(output)

def unmount():
	for dir in stream_dirs:
		print("Unmounting "+local_root+dir)
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
