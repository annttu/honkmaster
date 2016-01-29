# Lapio module. Transfer messages from channel 1 to channel 2

from plugins.honkplugin import HonkPlugin
import time
from datetime import date
import re

hashtag_regexp = re.compile(r"(\s|^)#\w+(\s|$)")

class Lapio(HonkPlugin):
    __name__ = "lapio"
    __target__ = "#log"

    def _plugin_init(self):
        print("Lapio started")
        if not self._irc_client.join_channel(self.__target__):
            print("Join failed :/")
            return
        print("Joined to channel %s" % self.__target__)
        self._irc_client.send_message("Lapio started", self.__target__)
        self._irc_client.send_message("Lapio started, logging to %s" % self.__target__)


    def process_incoming(self, message):
        print("%s" % (message,))
        if message['action'] != 'PRIVMSG':
            return
        if message['target'] == self.__target__:
            return
        who = message['source'].split('@')[0].split("!")[0]

        if not hashtag_regexp.search(message['data']):
            return

        # OMG #HASHTAG!!!!

        msg = message['data']

        year, week, weekday = date.today().isocalendar()

        msg = "%s #year%s #week%s" % (msg, year, week)

        print("Logging message: %s" % msg)

        self._irc_client.send_message("%s: %s" % (who, msg), channel=self.__target__)
