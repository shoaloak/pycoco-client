import logging
import time

from bytefifo import byteFIFO
from jacococlient import JacocoClient
from helpers import bool2byte
from datainput import read_char, read_UTF, read_long, read_bool_array

RECV_RETRIES = 3
#RECV_WAIT    = 0.01
RECV_WAIT    = 0.1

CMD_DUMP     = b'\x40'
MAGIC_NUM    = b'\xc0\xc0'
FORMAT_VER   = b'\x10\x07'
BLK_HEADER   = b'\x01'
BLK_SESSINFO = b'\x10'
BLK_EXECDATA = b'\x11'
BLK_END      = b' '

class ExecutionDataHandler():

    def __init__(self, jc: JacocoClient):
        self.first_block = True
        self.buf = byteFIFO()
        self.session_info_visitor = None
        self.execution_data_visitor = None

        self.jc = jc

    def read_header(self):
        if read_char(self.recv) != MAGIC_NUM:
            raise Exception("Invalid execution data file.")
        if read_char(self.recv) != FORMAT_VER:
            raise Exception("Incompatible version.")

    def set_session_info_visitor(self, visitor):
        if not callable(visitor):
            raise Exception(f"{visitor} is not a function.")
        self.session_info_visitor = visitor

    def set_execution_data_visitor(self, visitor):
        if not callable(visitor):
            raise Exception(f"{visitor} is not a function.")
        self.execution_data_visitor = visitor

    def read_session_info(self):
        if not (hasattr(self, 'session_info_visitor') or self.session_info_visitor):
            raise Exception("No session_info_visitor set.")
        id = read_UTF(self.recv)
        start = read_long(self.recv)
        dump = read_long(self.recv)
        self.session_info_visitor({'id': id, 'start':start, 'dump':dump})

    def read_execution_data(self):
        if not (hasattr(self, 'execution_data_visitor') or self.execution_data_visitor):
            raise Exception("No execution_data_visitor set.")
        id = read_long(self.recv)
        name = read_UTF(self.recv)
        probes = read_bool_array(self.recv)
        self.execution_data_visitor({'id': id, 'name':name, 'probes':probes})

    def read_block(self, block_type):
        if block_type == BLK_HEADER:
            # logging.debug("receiving header")
            self.read_header()
            return True
        elif block_type == BLK_SESSINFO:
            # logging.debug("receiving ses info")
            self.read_session_info()
            return True
        elif block_type == BLK_EXECDATA:
            # logging.debug("receiving exec data")
            self.read_execution_data()
            return True
        elif block_type == BLK_END:
            return False
        else:
            raise Exception(f"Unknown block type {block_type}")

    def recv(self, nbytes):
        retries = RECV_RETRIES

        # if the no. requested bytes is not there, retrieve
        while len(self.buf) < nbytes:
            newdata = self.jc.q2buf()
            if len(newdata) > 0:
                self.buf.put(newdata.getvalue())
            
            # still not enough and retries, wait
            if len(self.buf) < nbytes and retries > 0:
                retries -= 1
                time.sleep(RECV_WAIT)

            if retries == 0:
                raise Exception("Data did not arrive in time!")


        # # if empty, get new buffered data from JacocoClient
        # while len(self.buf) == 0 and retry > 0:
        #     self.buf = self.jc.q2buf()

        #     if len(self.buf) == 0:
        #         # still empty, wait and decrease retries
        #         time.sleep(0.1)
        #         retry -= 1

        # # it's still empty, stop
        # if len(self.buf) == 0:
        #     return False

        # return received bytes
        return self.buf.get(nbytes)

    def read(self):
        while True:
            data = self.recv(1)
            if not data:
                logging.warn("no data")
                return False

            block_type = data
            if self.first_block and block_type != BLK_HEADER:
                raise Exception("Invalid execution data file.")

            self.first_block = False
            if not self.read_block(block_type):
                break
        
        return True

    def visit_dump_command(self, dump: bool, reset: bool):
        msg = BLK_HEADER + MAGIC_NUM + FORMAT_VER
        msg += CMD_DUMP + bool2byte(dump) + bool2byte(reset)
        self.jc.sendq.put(msg)
