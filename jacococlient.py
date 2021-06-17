import logging
import queue
import select
import socket
import sys
import threading
import time

from bytefifo import byteFIFO

BUF_SIZE = 4096

class JacocoClient(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.runnable = True

        self.host = host
        self.port = port
        self.recvq = queue.Queue()
        self.sendq = queue.Queue()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.socket.setblocking(False)
        self.socket.settimeout(0.5)

    def run(self):
        self.socket.connect((self.host, self.port))

        while self.runnable:
            try:
                # poll() is unfortunately not supported by Windows
                readable, writable, exceptable = select.select(
                    [self.socket], [self.socket], [self.socket])

                if not (readable, writable, exceptable):
                    # optimization
                    continue

                if writable and not self.sendq.empty():
                    logging.debug("sending!")
                    self.socket.sendall(self.sendq.get())

                if readable:
                    logging.debug("receiving!")
                    data = self.socket.recv(BUF_SIZE)
                    if data:
                        self.recvq.put(data)

                if exceptable:
                    logging.debug("sending!")
                    print(f"{self.socket} is exceptable")
                    self.socket.close()
                    raise Exception("s was in the exception list")

            except KeyboardInterrupt:
                self.socket.close()
                break

    def q2buf(self):
        buf = byteFIFO()
        while True:
            time.sleep(0.5)
            if self.recvq.empty():
                break
            logging.debug("dit gaat mis?")
            buf.put(self.recvq.get())
        logging.debug("denk het")
        return buf






# while True:
#     if not recvq.empty():
#         data = recvq.get()

#         id = int.from_bytes(data[:8], 'big')
#         name = readUTF(data[8:])

#         print('id should be 0xCB64F06F06B03DAA')
#         print(data[:8])
#         print(id)
#         print(name)
#         sys.exit(-1)


        # print(data)
        # print(f"%016x  %3d of %3d   %s%n",
        #     Long.valueOf(data.getId()),
        #     Integer.valueOf(getHitCount(data.getProbes())),
        #     Integer.valueOf(data.getProbes().length),
        #     data.getName());

		# final long id = in.readLong();
		# final String name = in.readUTF();
		# final boolean[] probes = in.readBooleanArray();
		# executionDataVisitor
		# 		.visitClassExecution(new ExecutionData(id, name, probes));

