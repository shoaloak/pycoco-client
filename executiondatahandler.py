import logging

from bytefifo import byteFIFO
from jacococlient import JacocoClient
from helpers import bool2byte

CMD_DUMP = b'\x40'

MAGIC_NUM = b'\xc0\xc0'
FORMAT_VER = b'\x10\x07'

BLK_HEADER = b'\x01'
BLK_SESSINFO = b'\x10'
BLK_EXECDATA = b'\x11'

class ExecutionDataHandler():

    def __init__(self, jc: JacocoClient):
        self.first_block = True
        self.buf = byteFIFO()

        self.jc = jc

    def read_char(self):
        ch1 = self.recv(1)
        ch2 = self.recv(1)

        if (int(ch1[0] | ch2[0])) < 0:
            raise Exception()
        #return (ch2 + ch1).decode('utf-16')
        #return ch2+ch1
        return ch1+ch2

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
        if hasattr(self, 'session_info_visitor'):
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
            print("reading header")
            self.read_header()
            return True
        elif block_type == BLK_SESSINFO:
            print("reading ses info")
            self.read_session_info()
            return True
        elif block_type == BLK_EXECDATA:
            print("reading exec data")
            self.read_execution_data()
            return True
        else:
            raise Exception(f"Unknown block type {block_type}")

    def recv(self, nbytes=1):
        logging.debug("receiving!")
        if len(self.buf) == 0:
            # if empty, get new buffered data from JC

            logging.debug("getting new buffered data!")
            self.buf = self.jc.q2buf()
            logging.debug("DONE getting new buffered data!")

            if len(self.buf) == 0:
                return False

        logging.debug(f"getting {nbytes} bytes")
        return self.buf.get(nbytes)

    def read(self):
        while True:
            data = self.recv(1)
            if not data:
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
