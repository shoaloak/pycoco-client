#!/usr/bin/env python3
import logging
import time

from jacococlient import JacocoClient
from executiondatahandler import ExecutionDataHandler

logging.basicConfig(level=logging.DEBUG)

HOST = ''
PORT = 6300

def visit_session_info(info):
    print(info)

def main():
    jc = JacocoClient(HOST, PORT)
    handler = ExecutionDataHandler(jc)
    handler.set_session_info_visitor(visit_session_info)
    jc.start()

    print("wait for header to arrive")
    time.sleep(0.1)
    handler.read()

    print("sending dmp command")
    handler.visit_dump_command(True, True)
    time.sleep(0.1)
    handler.read()

    jc.runnable = False
    jc.join()
    print("fin.")

if __name__ == '__main__':
    main()
