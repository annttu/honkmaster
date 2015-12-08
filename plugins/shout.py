# Shout module. Transfer messages from socket to irc

from plugins.honkplugin import HonkPlugin
import time
from datetime import date
import socket
from select import select


class Shout(HonkPlugin):
    __name__ = "Shout"

    def _plugin_init(self):
        self.process_messages = False
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 5)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)

        self.s.bind(("localhost", 5555))
        self.s.listen(5)
        self._irc_client.send_message("%s started" % self.__name__)

        self.conns = []
        self.data = {}


    def send_buffer(self, conn):
        if '\n' in self.data[conn]:
            while self.data[conn]:
                p = self.data[conn].find('\n')
                self._irc_client.send_message("%s\n" % self.data[conn][:p])
                self.data[conn] = self.data[conn][p+1:]

    def loop(self):

        cont = True
        while cont and self._running:
            (readers,writers,errors) = select(self.conns + [self.s], self.conns, [self.s] + self.conns, 5)
            for r in readers:
                if r == self.s:
                    conn, addr = self.s.accept()
                    print("%s connected" % (addr,))
                    self.data[conn] = ""
                    self.conns.append(conn)
                else:
                    b = r.recv(4096).decode("utf-8", "ignore")
                    if len(b) == 0:
                        self.conns.remove(r)
                        r.close()
                        continue
                    self.data[conn] += b
                    self.send_buffer(conn)

            for x in errors:
                if x == self.s:
                    print("Server socket closed")
                    cont = False
                else:
                    self.conns.remove(x)
                    x.close()

        self.s.close()
