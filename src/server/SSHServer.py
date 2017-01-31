import paramiko
import threading

class SSHServer(paramiko.ServerInterface):
    def __init__(self, authorized_keys_filename):
        self.authorized_keys_filename = authorized_keys_filename
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_publickey(self, username, key):
        print('[Server] Auth attempt with key: ' + str(key.get_base64()))

        authorized_keys = open(self.authorized_keys_filename, "r")
        lines = authorized_keys.readlines()
        authorized_keys.close()

        for line in lines:
            print("[Server] Comparing "+line+" to "+key.get_base64())
            if key.get_base64() in line and username in line:
                print("[Server] Valid key")
                return paramiko.AUTH_SUCCESSFUL
        print("[Server] Invalid key")
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'gssapi-keyex,gssapi-with-mic,password,publickey'