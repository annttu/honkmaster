import os
import threading
import time

class HonkPlugin(threading.Thread):
    __name__ = "Unnamed plugin"

    def __init__(self, irc_client):
        threading.Thread.__init__(self)
        self._running = False
        self._irc_client = irc_client
        self.process_messages = True
        self._incoming = []

        self._plugin_init()

    def _plugin_init(self):
        pass

    def abort(self):
        self._running = False

    def incoming(self, message):
        if not self.process_messages:
            return
        self._incoming.append(message)

    def process_incoming(self, message):
        return

    def loop(self):
        return

    def run(self):
        self._running = True

        print("Plugin %s started" % str(self))

        try:
            while self._running:
                if self._incoming:
                    data = self._incoming.pop()
                    self.process_incoming(data)

                else:
                    self.loop()
                    time.sleep(0.1)
        except Exception as e:
            self._irc_client.send_message("Oh no, plugin %s is dead!" % str(self))
            raise
        
    def __str__(self):
        return self.__name__