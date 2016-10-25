import threading
import time
import os, subprocess
from watchdog.events import FileDeletedEvent, DirDeletedEvent

rsync_options = "-rltuvP --progress --exclude=\".Trash*\""

class FileSynchronizer (threading.Thread):
	def __init__(self, thread_id, task_queue): # , localRoot, remoteRoot):
		threading.Thread.__init__(self)
		self.thread_id = thread_id
		self.tasks = task_queue
		self.keep_running = True
		self.daemon = True
		# self.localRoot = os.path.abspath(localRoot)
		# self.remoteRoot = os.path.abspath(remoteRoot)

	def run(self):
		while self.keep_running:
			time.sleep(1)
			task = self.tasks.get(block=True)
			print("[Synchronizer] Thread " + str(self.thread_id) + " would now do " + str(task))
			#from, to =
			self.sync(task) # task["source"], task["destination"])
			self.tasks.task_done()

	def sync(self, event): # source, destination):
		print('Event: '+str(event))

		destination = event.dest_path + ("/" if event.is_directory else "")
		if (isinstance(event, FileDeletedEvent)
				or isinstance(event, DirDeletedEvent)):
			command = ["rm", destination]
		else:
			source = event.src_path + ("/" if event.is_directory else "")
			command = ["rsync", "-rltuvP", "--progress", "--exclude=\".Trash*\"", source, destination]

		# if isinstance(event, 'FileSystemMovedEvent'):
		# 	destination = event.dest_path + ("/" if event.is_directory else "")
		# 	source = self.localPathToRemote(source)
		# 	destination = self.localPathToRemote(destination)
		# elif (	isinstance(event, 'FileModifiedEvent')
		# 		or isinstance(event, 'DirModifiedEvent')
		# 		or isinstance(event, 'FileCreatedEvent')
		# 		or isinstance(event, 'DirCreatedEvent')):
		#
		# elif (isinstance(event, 'FileDeletedEvent')
		# 		or isinstance(event, 'DirDeletedEvent')):

		# else:
		#	return


		try:
			print(command)
			subprocess.check_output(command)
		except subprocess.CalledProcessError as error:
			print("[Synchronizer] Failed command: "+str(error))

	# def remotePathToLocal(self, remotePath):
	# 	relative_path = os.path.relpath(remotePath, self.remoteRoot)
	# 	return os.path.join(self.localRoot, relative_path)