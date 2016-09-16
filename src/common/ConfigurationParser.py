import argparse
import os
import sys
#Python 3
#import configparser
import configparser

def get_parameter_generic(config_path, config, section, option):
	if not config.has_option(section, option):
		#Python 3
		#configuration = input(option + ": ")
		#Python 2
		configuration = input(option + ": ")

		config.set(section, option, configuration)
		with open(config_path, "w") as configfile:
			config.write(configfile)

def get_parameter(config_path, config, section, option):
	get_parameter_generic(config_path, config, section, option)
	return config.get(section, option)

def get_parameter_boolean(config_path, config, section, option):
	get_parameter_generic(config_path, config, section, option)
	return config.getboolean(section, option)

def parse_config(exec_path=os.path.abspath(sys.argv[0]), config_path=os.path.abspath(os.path.join(sys.argv[0], "../SimpleCloud.conf"))):
	#global username, address, remote_root, local_root, stream_dirs, ssh_options, use_password
	#exec_path = os.path.abspath(sys.argv[0])
	configuration = {}

	#config_path = os.path.abspath( os.path.join(exec_path, "../../../SimpleCloud.conf"))
	configuration["sync_path"] = sync_path = os.path.abspath( os.path.join(exec_path, "../../sync/"))
	print("Config path: "+config_path)
	print("Sync path: "+sync_path)

	#Python 3
	#config = configparser.ConfigParser()
	#Python 2
	config_file = configparser.ConfigParser()
	config_file.read(config_path)

	configuration["user"] 			= config_file.get("Network","user") #get_parameter(config_path, config, "Network", "user")
	configuration["host"]		  	= config_file.get("Network", "host")
	configuration["port"] 			= int(config_file.get("Network", "port"))
	configuration["ssh_options"]  	= config_file.get("Network", "ssh_options")
	configuration["use_password"] 	= config_file.getboolean("Network", "use_password")
	
	configuration["stream_dirs"] 	= []
	for path,mountpoint in config_file.items("Stream Directories"):
		configuration["stream_dirs"].append({ "path" : path, "mountpoint" : mountpoint })
	
	configuration["sync_dirs"] = []
	for remote,local in config_file.items("Sync Directories"):
		#sync_path = configuration["sync_path"]
		mountpoint = os.path.abspath(os.path.join(sync_path, os.path.relpath(remote, "/")))
		configuration["sync_dirs"].append({ "path" : remote, "mountpoint" : sync_path+remote, "local" : local })
	
	return configuration
