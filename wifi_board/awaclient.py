import subprocess
from shlex import split
from time import sleep
import socket
try:
    from subprocess import run
except ImportError:
    from subprocess import check_call as run


class Awaclient():

    def __init__(self, port, ipc_port, identity, secret):
        self.port = str(port)
        self.ipc_port = str(ipc_port)
        self.identity = identity
        self.secret = secret

    def start_client(self, client_name='test'):
        cmd = "awa_clientd --port "+self.port+" --ipcPort "+self.ipc_port+" --endPointName "+ client_name +" --bootstrap coaps://deviceserver.creatordev.io:15684 --pskIdentity="+self.identity+" --pskKey="+self.secret
        subprocess.Popen(split(cmd))
        sleep(10)
        pass

    def create_object(self, arg):
        """
        Create an object on the client, argument is the options of the object/resource
        e.g. "--objectID=3200 --objectName='Digital Input' --resourceID=5501 --resourceName='Digital Input Counter' --resourceType=integer --resourceInstances=single --resourceRequired=optional --resourceOperations=r"
        """
        cmd = "awa-client-define --ipcPort="+self.ipc_port+" "+str(arg)
        run(split(cmd))

    def create_resource(self, path):
        """
        Create a instance/resource, argument is the path to instance/resource
        e.g. "/3200/0" instance 0 of object 3200
         "/3200/0/5501" resource 5501 on instance 0 of object 3200
        """
        cmd = "awa-client-set -p "+self.ipc_port+" --create "+str(path)
        run(split(cmd))

    def set_resource(self, path, value):
        """
        Set value for a resource
        """
        cmd = "awa-client-set -p "+self.ipc_port+" "+ str(path) +"="+str(value)
        run(split(cmd))

    def subscribe(self, path):
        """
        Subscribe to a resource value, when the value is changed on the server,
        the client will receive a notification
        """
        cmd = "awa-client-subscribe -p "+self.ipc_port+" "+str(path)
        subprocess.Popen(split(cmd))

    def handler(self):
        """
        Handler of the notification of a subscription
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
        s.bind(('127.0.0.1', int(self.ipc_port)))
        while True:
            data, address = s.recvfrom(65536)
            print(str(data))
            if "<Notification>" in str(data):
                print("Received Notification")
                self.handler_func()

    def handler_func(self):
        pass

