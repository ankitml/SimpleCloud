from watchdog.events import LoggingEventHandler as LoggingEventHandler_super, FileSystemEventHandler as FileSystemEventHandler_super
import os
import time

class FileSystemEventHandler(FileSystemEventHandler_super):
	def __init__(self, localRoot, remoteRoot, tasks):
		FileSystemEventHandler_super.__init__(self)
		self.localRoot = os.path.abspath(localRoot)
		self.remoteRoot = os.path.abspath(remoteRoot)
		self.tasks = tasks
		#self.rootPattern = re.compile(localRoot)
		print("[Handler] My root is " + self.localRoot + " and I send to " + remoteRoot)
	# def on_any_event(self, event):
    #    print "An event of type " + event.event_type + " occured on " + ("directory " if event.is_directory else "file ") + event.src_path
	def on_modified(self, event):
		print("[Handler] Modified: " + event.src_path)
		#relativepath = self.rootPattern.sub('', event.src_path)
		#relativePath = os.path.relpath(event.src_path, self.localRoot)
		#sendTo = os.path.join(self.remoteRoot, relativePath)
		sendTo = self.localPathToRemote(event.src_path)
		print("[Handler] Sending to " + sendTo)
		self.tasks.put(event.src_path+" => "+sendTo, block=True)
		
	def localPathToRemote(self, localPath):
		relativePath = os.path.relpath(localPath, self.localRoot)
		return os.path.join(self.remoteRoot, relativePath)

class LoggingEventHandler(LoggingEventHandler_super):
	pass
