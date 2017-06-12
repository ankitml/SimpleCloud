import queue
import selectors
import threading
import time

from tests.SSHCommunication import Client
from tests.SSHCommunication.Paramiko import Server


def serverStuff(myQueue):
    selector = selectors.DefaultSelector()
    channel = Server.getChannel()
    selector.register(channel, selectors.EVENT_READ, data="channel #"+str(channel.get_id()))
    while True:
        try:
            task = myQueue.get(timeout=0.1)
            print("[Server] "+str(task))
        except queue.Empty: pass
        events = selector.select(timeout=0.1)
        for key,mask in events:
            channel = key.fileobj
            data = channel.recv(1024)
            if not data:
                channel.close()
                print("[Server] Channel broken")
                exit()
            print("[Server] "+str(data))

def read(channel, event):
    pass

def connect():
    numMessage = 0
    myQueue = queue.Queue()
    myThread = threading.Thread(target=serverStuff, args=[myQueue])
    myThread.start()
    channel = Client.getChannel()
    while True:
        op = input("1 - queue, 2 - channel, else - quit\n > ")
        numMessage += 1
        myStr = "Communication #" + str(numMessage)
        if op=="1":
            myQueue.put(myStr)
        elif op=="2":
            channel.sendall(myStr)
        else:
            break
        time.sleep(1)
    channel.close()

if __name__ == "__main__":
    connect()