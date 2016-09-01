import socket
import ssl

#Server
class TaskEmitter:
	def __init__(self, host, port):
		self.TCPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.TCPsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.TCPsocket.bind((host, port))
		self.TCPsocket.listen(10)
		
		self.SSLsocket = ssl.wrap_socket(self.TCPsocket, ssl_version=ssl.PROTOCOL_TLSv1)#, ciphers="ADH-AES256-SHA")
		#self.SSLsocket.bind((host, port))
		#self.SSLsocket.listen(10)
	
	def __del__(self):
		self.close()
	
	def open(self):
		print "Awaiting client..."
		#self.client_connection,self.client_address = self.SSLsocket.accept()
		self.client_connection,self.client_address = self.TCPsocket.accept()
		print "Connected to "+str(self.client_address)
		
		#while True:
		#	data = conn.recv(1024)
		#	if not data: break
		#	print data
		
	def close(self):
		print "Closing server"
		#self.SSLsocket.close()
		self.TCPsocket.close()
	
	def send(self, packet):
		self.client_connection.sendall(packet)

def test():
	host = "localhost"
	port = 1507
	emitter = TaskEmitter(host, port)
	emitter.open()
	
	while True:
		print "Enter your packet:"
		packet = raw_input()
		emitter.send(packet)

test()
