import socket
import ssl

#Client
class TaskReceiver:
	def __init__(self, host, port):
		self.host = host
		self.port = port
		
		self.TCPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.TCPsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		
		#self.SSLsocket = ssl.wrap_socket(self.TCPsocket, ssl_version=ssl.PROTOCOL_TLSv1)#, ciphers="ADH-AES256-SHA")
	
	def __del__(self):
		self.close()
		
	def connect(self):
		#self.SSLsocket.connect((self.host, self.port))
		self.TCPsocket.connect((self.host, self.port))
		print "Connected to "+str(self.host)+":"+str(self.port)
		
		while True:
			data = self.TCPsocket.recv(1024)
			if not data: break
			print data
		
	def close(self):
		print "Closing client"
		#self.SSLsocket.close()
		self.TCPsocket.close()

def test():
	host = "localhost"
	port = 1507
	
	receiver = TaskReceiver(host, port)
	print "Created receiver"
	receiver.connect()

test()
