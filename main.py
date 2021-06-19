#!/usr/bin/env python3
import logging
import threading
import time

from jacococlient import JacocoClient
from executiondatahandler import ExecutionDataHandler

logging.basicConfig(level=logging.DEBUG)

HOST = ''
PORT = 6300

def visit_session_info(info):
    print(info)

def visit_execution_data(data):
    print(data)

def main():
    connect_event = threading.Event()

    # setup client thread and the handler
    jc = JacocoClient(connect_event, HOST, PORT)
    handler = ExecutionDataHandler(jc)
    handler.set_session_info_visitor(visit_session_info)
    handler.set_execution_data_visitor(visit_execution_data)

    # start thread and wait until connected
    jc.start()
    connect_event.wait(timeout=1)
    if not connect_event.is_set():
        return

    if not handler.read():
        raise Exception("Incomplete header")

    logging.info("sending dmp command")
    handler.visit_dump_command(True, True)
    time.sleep(0.01)
    while True:
        if handler.read():
            break

    handler.read()

    # wait and close
    time.sleep(0.1)
    jc.runnable = False
    jc.join()
    print("fin.")

if __name__ == '__main__':
    main()
