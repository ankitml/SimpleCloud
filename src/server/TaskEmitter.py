import socket
import ssl
import time
import threading
import pickle
import queue

#Server
class TaskEmitter(threading.Thread):
	def __init__(self, host, port, task_queue):
		threading.Thread.__init__(self)
		self.tasks = task_queue

		self.TCPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.TCPsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.TCPsocket.bind((host, port))
		self.TCPsocket.listen(10)
		self.watch_queue = threading.Event()
		
		#self.SSLsocket = ssl.wrap_socket(self.TCPsocket, ssl_version=ssl.PROTOCOL_TLSv1)#, ciphers="ADH-AES256-SHA")
		#self.SSLsocket.bind((host, port))
		#self.SSLsocket.listen(10)
	
	def run(self):
		print("Awaiting client...")
		#self.client_connection,self.client_address = self.SSLsocket.accept()
		self.client_connection,self.client_address = self.TCPsocket.accept()
		print("[Emitter] Connected to " + str(self.client_address))
		self.register_client()

		self.watch_queue.wait()
		while self.watch_queue.is_set():
			try:
				data = self.tasks.get(block=True, timeout=1)
			except queue.Empty: continue
			self.tasks.task_done()
			print("[Emitter] Received " + str(data) + " from task queue")
			self.client_connection.sendall(pickle.dumps(data))

	def register_client(self):
		sync_dirs = pickle.loads(self.client_connection.recv(1024))
		self.tasks.put(sync_dirs)
		
	def join(self):
		print("Closing server")
		self.watch_queue.clear()
		#self.raise(MyException)
		#self.SSLsocket.close()
		self.TCPsocket.close()

class MyException(Exception):
	def __init__(self):
		Exception.__init__(self)
