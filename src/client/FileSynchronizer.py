import threading
import time
import Queue

# Use deque.append() and deque.popleft() as these are thread-safe

class FileSynchronizer (threading.Thread):
	def __init__(self, thread_id, task_queue):
		threading.Thread.__init__(self)
		self.thread_id = thread_id
		self.tasks = task_queue
		self.daemon = True

	def run(self):
		while True:
			print "I am a thread"
			time.sleep(1)
			task = self.tasks.get(block=True)
			#print "[Thread] Thread "+str(self.thread_id)+" would now do"+task