# General tools
import os
import logging
import time
import paramiko

# Multi-threading tools
from queue import Queue

from src.common import ConfigurationParser
from watchdog.observers import Observer
from .TaskEmitter import TaskEmitter
from src.server.ClientRegistrar import ClientRegistrar
from src.server.ClientIndex import ClientIndex

def get_config():
    global parameters, tasks
    parameters = ConfigurationParser.parse_config()
    print("Parameters: " + str(parameters))

def register_client():
    global emitters, clients
    emitters = []
    registry = ClientIndex

    registrar = ClientRegistrar(
        parameters["host"], parameters["port"], clients,
        parameters["private_key_file"], parameters["authorized_keys_file"])

    emitter = TaskEmitter(client_connection, tasks)
    emitter.start()
    emitters.append(emitter)
    emitter.watch_queue.set()

    watch_queues(sync_dirs)

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

global parameters, observer, emitters, tasks, clients
tasks = Queue()
clients = Queue()

get_config()
register_client()
#connect()
#watch()

exit()