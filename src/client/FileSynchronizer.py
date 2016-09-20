import threading
import time
import subprocess

rsync_options = "-rltuvP --progress --exclude=\".Trash*\""

class FileSynchronizer (threading.Thread):
	def __init__(self, thread_id, task_queue):
		threading.Thread.__init__(self)
		self.thread_id = thread_id
		self.tasks = task_queue
		self.keep_running = True
		self.daemon = True

	def run(self):
		while self.keep_running:
			time.sleep(1)
			task = self.tasks.get(block=True)
			print("[Synchronizer] Thread " + str(self.thread_id) + " would now do " + str(task))
			#from, to =
			self.send(task["source"], task["destination"])
			self.tasks.task_done()

	def send(self, source, destination):
		rsync_command = ["rsync", "-rltuvP","--progress","--exclude=\".Trash*\"", source, destination]
		try:
			print(rsync_command)
			subprocess.check_output(rsync_command)
		except subprocess.CalledProcessError as error:
			print("[Synchronizer] Failed rsync command: "+str(error))