import collections
import logging

from telnetlib3.telsh import Telsh, TelnetShellStream


def telnet2cmd(func):
    def wrapped(*args):
        return func(' '.join(args))
    return wrapped


class BoundStream():

    def __init__(self, stream):
        self.stream = stream

    def __getattr__(self, item):
        return getattr(self.stream, item)

    def write(self, text):
        self.stream.write(text.replace('\r\n', '\n').replace('\n', '\r\n'))


class HistoryTelsh(Telsh):

    def __init__(self, server, stream=TelnetShellStream, log=logging):
        super().__init__(server, stream, log)
        self.save = 0
        self.cmd_index = 0
        self.history = []
        self.act_cmd = None

    def inc_index(self, num):
        self.cmd_index += num
        self.cmd_index = max(0, self.cmd_index)
        self.cmd_index = min(len(self.history), self.cmd_index)

    def paste_history(self):
        if self.history:
            self._lastline.clear()
            self.display_prompt(redraw=True)
            hist = ((self.act_cmd if self.act_cmd else collections.deque(''))
                    if self.cmd_index == len(self.history) else
                    collections.deque(self.history[self.cmd_index]))
            self.stream.write(''.join(list(hist)))
            self._lastline = hist.copy()

    def character_received(self, char, literal=False):
        if char in ('\x1b',):
            self.save = 3
        if self.save > 0:
            self.save -= 1
            if self.save == 0:
                if char == 'A':
                    if self.cmd_index == len(self.history):
                        self.act_cmd = self._lastline.copy()
                    self.inc_index(-1)
                    self.paste_history()
                elif char == 'B':
                    self.inc_index(1)
                    self.paste_history()
            return
        return super().character_received(char, literal)

    def line_received(self, input):
        return super().line_received(input)

    def process_cmd(self, input):
        self.history.append(input)
        self.cmd_index = len(self.history)
        return super().process_cmd(input)


class CmdTelsh(HistoryTelsh):

    def __init__(self, server, stream=TelnetShellStream, log=logging,
                 cmd=None):
        super().__init__(server, stream, log)
        self.cmd = cmd
        cmd_prefix = 'do_'
        for name in filter(lambda x: x.startswith(cmd_prefix),
                           self.cmd.get_names()):
            command = name[len(cmd_prefix):]
            target_cmd = telnet2cmd(getattr(self.cmd, name))
            setattr(self, self.cmd_prefix + command, target_cmd)
        prompt = self.cmd.prompt
        self.server.env_update({'PS1': prompt, 'PS2': prompt})
        self.cmd.stdout = BoundStream(self.stream)
