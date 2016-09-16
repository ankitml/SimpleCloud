import time
from watchdog.observers import Observer
from .EventHandler import FileSystemEventHandler

def getObserver(sync_dirs, task_queue):
	observer = Observer()
	for sync in sync_dirs:
		local = sync["local"]
		remote = sync["remote"]
		print("[Observer] I observe "+local+" and send to "+remote)

		handler = FileSystemEventHandler(local, remote, task_queue)
		observer.schedule(handler, local, recursive=True)
	return observer

def start(observer):
	observer.start()
	try:
		while True:
			print("Watching, waiting")
			time.sleep(1)
	except KeyboardInterrupt:
		print("This should print")
		observer.stop()
	observer.join()
			#while not tasks.empty():
			#	task = tasks.get(block=True)
			#	print task
def stop(observer):
	observer.stop()
	observer.join()