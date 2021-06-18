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

    # logging.info("wait for header to arrive")
    # time.sleep(0.0000001)
    if not handler.read():
        raise Exception("Incomplete header")

    logging.info("sending dmp command")
    handler.visit_dump_command(True, True)
    time.sleep(0.01)
    if handler.read():
        logging.info("Success")

    jc.runnable = False
    jc.join()
    print("fin.")

if __name__ == '__main__':
    main()
