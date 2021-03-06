#!/usr/bin/env python3
import logging
import sys
import threading
import time

from jacococlient import JacocoClient
from executiondatahandler import ExecutionDataHandler

logging.basicConfig(level=logging.INFO)

HOST = ''
PORT = 6300

def get_hit_count(probes):
    count = 0
    for probe in probes:
        if probe:
            count += 1
    return count

def visit_session_info(info):
    print(info)

def visit_execution_data(data):
    # TODO configurable filter
    # if data['name'].startswith('com.axelkoolhaas'):
    print(data['id'])
    print(data['name'])
    print(f"{get_hit_count(data['probes'])} of {len(data['probes'])}")


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
        logging.error(f"Could not connect to socket {HOST}{PORT}")
        sys.exit(-1)

    logging.info("sending dmp command")
    handler.visit_dump_command(True, True)

    #time.sleep(0.01)
    if not handler.read():
        raise Exception("Incomplete header")

    # wait and close
    time.sleep(0.2)
    jc.runnable = False
    jc.join()
    print("fin.")

if __name__ == '__main__':
    main()
