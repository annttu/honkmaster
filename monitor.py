import os
import threading
import time

class FileMonitor(threading.Thread):
    def __init__(self, logfile, irc_client):
        threading.Thread.__init__(self)
        self._running = False
        self._irc_client = irc_client
        self._filehandle = None
        self._logfile = logfile

    def abort(self):
        self._running = False

    def run(self):
        self._running = True
        
        self._filehandle = open(self._logfile, 'r')
        st_results = os.stat(self._logfile)
        st_size = st_results[6]
        ino = os.stat(self._filehandle.name).st_ino

        self._filehandle.seek(st_size)

        while self._running:
            gotline = False
            test_ino = ino
            try:
                test_ino = os.stat(self._filehandle.name).st_ino
            except:
                continue

            if ino != test_ino:
                try:
                    self._filehandle.close()
                    self._filehandle = open(self._logfile, 'r')
                except:
                    continue
                st_results = os.stat(self._logfile)
                st_size = st_results[6]
                ino = os.stat(self._filehandle.name).st_ino

            where = self._filehandle.tell()
            line = self._filehandle.readline()
            if not line:
                self._filehandle.seek(where)
            else:
                gotline = True

            if gotline:
                self._irc_client.send_message(line.strip())
            else:
                time.sleep(0.1)