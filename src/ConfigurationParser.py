import argparse
#Python 3
#import configparser
import ConfigParser

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
	#global username, address, remote_root, local_root, stream_dirs, ssh_options, use_password
	config_path = os.path.abspath("../SimpleCloud.conf")

	#Python 3
	#config = configparser.ConfigParser()
	#Python 2
	config_file = ConfigParser.ConfigParser()
	config_file.read(config_path)
	
	configuration = {}

	configuration{"username"} 		= get_parameter(config_path, config, "Network", "user")
	configuration{"address"} 		= get_parameter(config_path, config, "Network", "address")
	configuration{"stream_dirs"} 	= get_parameter(config_path, config, "Directories",
		"stream_directories")
	configuration{"remote_root"} 	= get_parameter(config_path, config, "Directories", "remote_root")
	configuration{"local_root"} 	= get_parameter(config_path, config, "Directories", "local_root")
	configuration{"ssh_options"} 	= get_parameter(config_path, config, "Network", "ssh_options")
	configuration{"use_password"} 	= get_parameter_boolean(config_path, config, "Network", "password")
		
	#	ssh_options+=" -o password_stdin"
