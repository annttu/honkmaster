#!/usr/bin/python

"""
Simple and ugly client for honkmaster2 shout plugin.

- Annttu

"""


import socket
import sys
import fileinput
import re

# P.s. https://regex101.com/ is your friend!

MESSAGES = {
    r'^(?P<date>\w+ \s?\d+ \d+:\d+:\d+) (?P<host>\S+) sudo: (?P<user>\S+) : TTY=pts\/\d+ ; PWD=\S+ ; USER=(?P<become>\S+) ; COMMAND=(?P<command>\S+)$': '\x02SUDO\x0F: %(host)s: %(user)s -> %(become)s command %(command)s',
    r'^(?P<date>\w+ \s?\d+ \d+:\d+:\d+) (?P<host>\S+) sudo: (?P<method>\S+): (?P<message>.+); logname=(?P<user>\S+) uid=\d+ euid=\d+ ': '\x02SUDO\x0F: %(host)s: %(user)s using %(method)s: %(message)s',
    r'^(?P<date>\w+ \s?\d+ \d+:\d+:\d+) (?P<host>\S+) sshd\[\d+\]: Accepted (?P<method>\S+) for (?P<user>\S+) from (?P<address>\S+) port \d+': '\x02SSH\x0F: %(host)s: user %(user)s login from %(address)s using %(method)s',
}


def pretty_log(message):
    for regexp, formatting in MESSAGES.items():
        try:
            x = re.match(regexp, message)
            if x:
                return(formatting % x.groupdict())
        except Exception as e:
            print("Regexp %s broken" % (regexp,))
    return message


class ShoutClient(object):
    def __init__(self, host="localhost", port=5555):
        self.host = host
        self.port = port
        self.connect()

    def connect(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Keepalive
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE,1)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)

        self.s.connect((self.host, self.port))

    def send_message(self, message):
        self.s.sendall('%s\n' % message.strip())

    def close(self):
        self.s.close()


def main():

    shout = ShoutClient()

    message = ""
    for arg in sys.argv[1:]:
        message = "%s %s" % (message, arg)

    if message:
        s.sendall('%s\n' % message.strip())

    line = ""
    while 1:
        x = sys.stdin.read(1)
        if not x:
            break
        line += x
        if '\n' in line:
            shout.send_message('%s\n' % pretty_log(line.strip()))
            line = ""
    if '\n' in line:
        shout.send_message('%s\n' % pretty_log(line.strip()))

    shout.close()


if __name__ == '__main__':
    main()