import pickle

import paramiko


#private_key = paramiko.RSAKey(filename="/home/francisco/.ssh/fake_key")
def getChannel():
    private_key = paramiko.RSAKey(filename="/home/francisco/.ssh/id_rsa")

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())
    client.connect('localhost', port=3509, pkey=private_key)
    # input, output, err = client.exec_command("ls -la")
    # for line in output.readlines():
    #     print(line)

    transport = client.get_transport()
    channel = transport.open_channel(kind="session")
    return channel

if __name__ == "__main__":
    channel = getChannel()
    while True:
        data = input("What would you like to send to the server?\n  > ")
        datab = pickle.dumps(data)
        channel.sendall(datab)
        responseb = channel.recv(1024*1024)
        response = pickle.loads(responseb)
        print("Server replied with:\n  "+response)