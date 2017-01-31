# General tools
import os
import logging
import time
import paramiko

# Multi-threading tools
from queue import Queue

from src.common import ConfigurationParser
import src.common.Observer as Observer
from .TaskEmitter import TaskEmitter

def get_config():
    global parameters, tasks
    parameters = ConfigurationParser.parse_config()
    print("Parameters: " + str(parameters))

def register_client():
    import socket, pickle
    global emitters

    emitters = []
    registrator = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    registrator.bind(('', parameters["port"]))
    registrator.listen(10)

    client_connection, client_address = registrator.accept()
    print("[Emitter] Connected to " + str(client_address))

    sync_dirs = pickle.loads(client_connection.recv(1024))
    print("Sync dirs: "+str(sync_dirs))

    emitter = TaskEmitter(client_connection, tasks)
    emitter.start()
    emitters.append(emitter)
    emitter.watch_queue.set()

    watch(sync_dirs)

def connect():
    global emitter, tasks
    emitter = TaskEmitter(parameters["host"], parameters["port"], tasks)
    emitter.start()

def watch(sync_dirs):
    global observer
    #parameters["sync_dirs"] = tasks.get(block=True)
    #tasks.task_done()

    for dir in sync_dirs: # parameters["sync_dirs"]:
        print("Observe " + dir["remote"] + " and send to " + dir["local"])
    observer = Observer.getObserver(sync_dirs, tasks) # (parameters["sync_dirs"], tasks)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping observer")
        emitter.join()
        observer.stop()
    observer.join()
    print("Here")

global parameters, observer, emitters, tasks
tasks = Queue()

get_config()
register_client()
#connect()
#watch()

exit()