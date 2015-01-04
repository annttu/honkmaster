import socket
import threading
import logging
import time

IRCStatusMap = {
    '001': 'WELCOME',
    '002': 'YOURHOST',
    '003': 'CREATED',
    '004': 'MYINFO',
    '005': 'PROTOCOL',
    '042': 'YOURID',
    '251': 'LUSERCLIENT',
    '252': 'LUSEROP',
    '253': 'LUSERUNKNOWN',
    '254': 'LUSERCHANNELS',
    '255': 'LUSERME',
    '265': 'LOCALUSERS',
    '266': 'GLOBALUSERS',
    '372': 'MOTD',
    '375': 'MOTDSTART',
    '376': 'ENDOFMOTD',
    '433': 'NICKINUSE'
}

class IRCException(BaseException):
    pass

class IRCClient(threading.Thread):
    def __init__(self, server, port, channel, nick, realname):
        threading.Thread.__init__(self)
        self._server = server
        self._port = port
        self._channel = channel
        self._nick = nick
        self._realname = realname

        self._running = False
        self._socket = None

        self._logger = logging.getLogger('IRCClient')

        self._incoming_mq = []
        self._outgoing_mq = []

        self._mq_lock = threading.Lock()

    def send_message(self, data):
        self._mq_lock.acquire()
        self._incoming_mq.append(data)
        self._mq_lock.release()

    def _process_messages(self):
        self._mq_lock.acquire()
        self._outgoing_mq = self._incoming_mq
        self._incoming_mq = []
        self._mq_lock.release()

        for message in self._outgoing_mq:
            self._send_to_channel(message)

        self._outgoing_mq = []

    def _encode_send(self, data):
        self._logger.debug("=> %s" % (data))
        self._socket.send(data.encode('utf-8'))

    def _decode_recv(self, len):
        data = self._socket.recv(4096).decode('utf-8')
        lines = data.split('\n')
        out_lines = []
        for line in lines:
            line = line.strip()
            if line != '':
                out_lines.append(line)
                self._logger.debug("<= %s" % (line))

        return out_lines

    def _parse_irc_lines(self, data):
        line_data = []
        for line in data:
            try:
                if line.startswith('PING'):
                    data = line.split(':')[1]
                    self._encode_send('PONG :%s' % (data))
                    self._logger.info("PING %s? PONG %s!" % (data, data))
                    continue

                source = None
                action = None
                target = None
                rest = None

                try:
                    source, action, target, rest = line.split(' ', 3)
                except:
                    source, action, target = line.split(' ', 3)

                if source.startswith(':'):
                    source = source[1:]

                if target.startswith(':'):
                    target = target[1:]

                if rest is not None and rest.startswith(':'):
                    rest = rest[1:]

                if action.isdigit():
                    if action in IRCStatusMap:
                        action = IRCStatusMap[action]
                    else:
                        action = 'UNK%s' % (action)

                line_data.append({'source': source, 'action': action, 'target': target, 'data': rest})

                if rest is not None:
                    self._logger.info("%s [%s -> %s] >> %s" % (source, action, target, rest))
                else:
                    self._logger.info("%s [%s -> %s]" % (source, action, target))
            except:
                self._logger.error(line)
                raise

        return line_data

    def _send_to_channel(self, message):
        self._encode_send('PRIVMSG %s :%s\r\n' % (self._channel, message))
        self._logger.info("%s [PRIVMSG -> %s] >> %s" % (self._nick, self._channel, message))

    def _initial_irc_connect(self):
        self._encode_send('NICK %s\r\n' % (self._nick))
        self._encode_send('USER %s %s %s :%s\r\n' % (self._nick, self._nick, self._nick, self._realname))

        motd_done = False
        join_done = False

        while not motd_done:
            irc_data = self._parse_irc_lines(self._decode_recv(4096))
            for data in irc_data:
                if data['action'] == 'NICKINUSE':
                    self._logger.error("IRC nick in use")
                    raise IRCException("IRC nick in use")

                if data['action'] == 'ENDOFMOTD':
                    motd_done = True

        self._encode_send('JOIN %s\r\n' % (self._channel))
        while not join_done:
            irc_data = self._parse_irc_lines(self._decode_recv(4096))
            for data in irc_data:
                if data['action'] == 'JOIN' and data['target'] == self._channel:
                    join_done = True

        self._send_to_channel('Hello :)')

    def _irc_loop(self):
        self._socket.setblocking(False)

        while self._running:
            got_data = False
            try:
                irc_data = self._parse_irc_lines(self._decode_recv(4096))
                got_data = True

                # implement custom event handlers here whenever
            except BlockingIOError as bie:
                pass

            self._process_messages()

            if not got_data:
                time.sleep(0.1)

    def abort(self):
        self._running = False
        self._socket.close()

    def run(self):
        self._running = True
        try:
            self._socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            self._socket.connect((self._server,self._port))
        except OSError as ose:
            self._logger.error("failed connecting when using AF_INET6, fallback to inet")

            try:
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.connect((self._server,self._port))
            except BaseException as e:
                self._logger.error("failed connecting when using AF_INET fallback")
                self._logger.exception(e)
                raise
        except BaseException as e:
            self._logger.error("failed connecting when using AF_INET6, weird exception!")
            raise

        try:
            self._initial_irc_connect()
            self._irc_loop()
        except IRCException as ie:
            self._socket.close()


