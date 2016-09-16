import threading
import time

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
			self.tasks.task_done()
