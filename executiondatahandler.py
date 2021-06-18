import logging
import time

from bytefifo import byteFIFO
from jacococlient import JacocoClient
from helpers import bool2byte

RECV_RETRIES = 3
RECV_WAIT    = 0.0001

CMD_DUMP     = b'\x40'
MAGIC_NUM    = b'\xc0\xc0'
FORMAT_VER   = b'\x10\x07'
BLK_HEADER   = b'\x01'
BLK_SESSINFO = b'\x10'
BLK_EXECDATA = b'\x11'

class ExecutionDataHandler():

    def __init__(self, jc: JacocoClient):
        self.first_block = True
        self.buf = byteFIFO()

        self.jc = jc

    def read_char(self):
        ch = self.recv(2)
        # ch2 = self.recv(1)

        if (int(ch[0] | ch[1])) < 0:
            raise Exception()
        #return (ch2 + ch1).decode('utf-16')
        #return ch2+ch1
        # return ch1+ch2
        return ch

    def read_ushort(self):
        return int.from_bytes(self.recv(2), 'big')
    
    def read_UTF(self):
        utflen = self.read_ushort()
        utf_string = self.recv(utflen)

        if len(utf_string) != utflen:
            raise Exception("UTF length mismatch")

        return utf_string.decode('utf-8')

    def read_long(self):
        return int.from_bytes(self.recv(8), 'big')

    def read_header(self):
        if self.read_char() != MAGIC_NUM:
            raise Exception("Invalid execution data file.")
        if self.read_char() != FORMAT_VER:
            raise Exception("Incompatible version.")

    def set_session_info_visitor(self, visitor):
        self.session_info_visitor = visitor

    def read_session_info(self):
        if not hasattr(self, 'session_info_visitor'):
            raise Exception("No session_info_visitor: set it.")
        id = self.read_UTF()
        start = self.read_long()
        dump = self.read_long()
        self.session_info_visitor({'id': id, 'start':start, 'dump':dump})

    def read_execution_data(self):
        #TODO
        pass

    def read_block(self, block_type):
        if block_type == BLK_HEADER:
            logging.debug("reading header")
            self.read_header()
            return True
        elif block_type == BLK_SESSINFO:
            logging.debug("reading ses info")
            self.read_session_info()
            return True
        elif block_type == BLK_EXECDATA:
            logging.debug("reading exec data")
            self.read_execution_data()
            return True
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
            if self.read_block(block_type):
                break
        
        logging.info("returning true")
        return True

    def visit_dump_command(self, dump: bool, reset: bool):
        msg = BLK_HEADER + MAGIC_NUM + FORMAT_VER
        msg += CMD_DUMP + bool2byte(dump) + bool2byte(reset)
        self.jc.sendq.put(msg)
