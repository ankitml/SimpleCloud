import socket
import ssl
import threading
import time
import pickle

#Client
class TaskReceiver(threading.Thread):
	def __init__(self, host, port, task_queue, sync_dirs):
		threading.Thread.__init__(self)
		self.daemon = True

		self.host = host
		self.port = port
		self.tasks = task_queue
		self.sync_dirs = sync_dirs
		
		self.TCPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.TCPsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		
		#self.SSLsocket = ssl.wrap_socket(self.TCPsocket, ssl_version=ssl.PROTOCOL_TLSv1)#, ciphers="ADH-AES256-SHA")
	
	def __del__(self):
		self.close()
		
	def run(self):
		#self.SSLsocket.connect((self.host, self.port))
		try:
			self.TCPsocket.connect((self.host, self.port))
			print("[Receiver] Connected to " + str(self.host) + ":" + str(self.port))
			self.register()

		except ConnectionRefusedError as error:
			print("Server not available at " + self.host + ":" + str(self.port))
			return

		while True:
			data = pickle.loads(self.TCPsocket.recv(1024))
			if not data: break
			print("[Receiver] Inserting "+str(data)+" into task queue")
			self.tasks.put(data, block=True)

	def register(self):
		remote_dirs = []
		for dir in self.sync_dirs:
			remote_dirs.append({
				"local": dir["remote"],
				"remote": dir["local"]
			})
		remote_dirs = pickle.dumps(remote_dirs)
		self.TCPsocket.sendall(remote_dirs)
		
	def close(self):
		print("Closing client")
		#self.SSLsocket.close()
		self.TCPsocket.close()

def test():
	import queue.Queue as Queue
	host = "localhost"
	port = 1507
	
	receiver = TaskReceiver(host, port, Queue())
	print("Created receiver")
	receiver.run()

#test()
