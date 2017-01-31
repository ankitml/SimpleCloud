import paramiko

#private_key = paramiko.RSAKey(filename="/home/francisco/.ssh/fake_key")
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

channel.send("ola")
channel.send("adeus")
transport.close()