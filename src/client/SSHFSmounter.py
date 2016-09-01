import subprocess
import shlex
import os

def mount (host, path, mountpoint, user=None, ssh_options=None):
	command = "sshfs "
	if user:
		command += user + "@"
	command += host + ":" + path + " " + mountpoint
	if ssh_options:
		command += " " + ssh_options
	#print command
	command = shlex.split(command)
	print "Mounting " + host+":"+path + " in " + mountpoint
	try:
		mkdir_recursive(mountpoint)
		subprocess.check_output(command)
	except subprocess.CalledProcessError as error:
		#print "Error mounting, code=" + str(error.returncode)
		raise MountingError(host+":"+path, mountpoint)
		

def unmount (mountpoint):
	print("\nUnmounting "+mountpoint)
	try:
		subprocess.check_output(["fusermount","-uz", mountpoint])
	except subprocess.CalledProcessError as error:
		#print "Error unmounting, code=" + str(error.returncode)
		raise UnmountingError(mountpoint)

def mkdir_recursive(path):
	sub_path = os.path.dirname(path)
	if not os.path.exists(sub_path):
		mkdir_recursive(sub_path)
	if not os.path.exists(path):
		os.mkdir(path)

#def rmdir_recursive(path)

class MountingError(Exception):
	def __init__(self, path, mountpoint):
		self.path = path
		self.mountpoint = mountpoint
	def __str__(self):
		return "Error mounting " + self.path + " in " + self.mountpoint

class UnmountingError(Exception):
	def __init__(self, mountpoint):
		self.mountpoint = mountpoint
	def __str__(self):
		return "Error unmounting " + self.mountpoint
