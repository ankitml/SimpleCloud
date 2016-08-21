import subprocess
import shlex

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
		subprocess.check_output(command)
	except subprocess.CalledProcessError, error:
		print "Error mounting, code=" + str(error.returncode)
		exit(1)
		

def unmount (mountpoint):
	print("\nUnmounting "+mountpoint)
	try:
		subprocess.check_output(["fusermount","-uz", mountpoint])
	except subprocess.CalledProcessError, error:
		print "Error unmounting, code=" + str(error.returncode)
