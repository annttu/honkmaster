# Shout module. Transfer messages from socket to irc

from plugins.honkplugin import HonkPlugin
import time
from datetime import date
import socket


class Shout(HonkPlugin):
    __name__ = "Shout"

    def _plugin_init(self):
        self.process_messages = False
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(("localhost", 5555))
        self.s.listen(1)
        self._irc_client.send_message("%s started" % self.__name__)
        

    def loop(self):
        conn, addr = self.s.accept()

        data = ""
        cont = True
        while cont:
            b = conn.recv(1024).decode("utf-8", 'ignore')
            if not b:
                cont = False
            data = "%s%s" % (data, b)
            if '\n' in data:
                self._irc_client.send_message("%s" % data)
                data = ""
        conn.close()
