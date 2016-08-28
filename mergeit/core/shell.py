import cmd
import logging
import re
import traceback

from structlog.dev import ConsoleRenderer

from mergeit.overrides.logging_extras import ProcessorFormatter


def multiarg(func):
    def wrapped(self, arg):
        try:
            return func(self, *(re.split(r'\s+', arg) if arg.strip() else []))
        except:
            print(traceback.format_exc())
    wrapped.__doc__ = func.__doc__
    return wrapped


class BaseShell(cmd.Cmd):

    def emptyline(self):
        pass

    def do_EOF(self, arg):
        print()
        return True


class MergeitShell(BaseShell):

    intro = 'Welcome to the merGeIT shell. Type help or ? to list commands.\n'
    prompt = 'mergeit>> '
    file = None

    def __init__(self, completekey='tab', stdin=None, stdout=None,
                 config=None, push_handler_factory=None, repo_manager_factory=None, forward=False):
        super().__init__(completekey, stdin, stdout)
        self.config = config
        self.push_handler_factory = push_handler_factory
        self.repo_manager_factory = repo_manager_factory
        self.forward = forward
        self.repo_manager = self.repo_manager_factory(config['name'],
                                                      config['uri'],
                                                      config['merge_workspace'])
        self.repo_manager.fetch()

    def get_logger_handler(self):
        logger_handler = logging.StreamHandler(self.stdout)
        formatter = ProcessorFormatter(
            ConsoleRenderer() # colorize=True
        )  # TODO: some kind of logging.getFormatter (using key, passed to dictConfig)?
        logger_handler.setFormatter(formatter)
        return logger_handler

    def precmd(self, line):
        self.config.reload()
        return super().precmd(line)

    @multiarg
    def do_fetch(self):
        self.repo_manager.fetch()

    def _complete_branches(self, text):
        branches = self.repo_manager.get_branches(True, fetch=False)
        return [branch for branch in branches if branch.startswith(text)]

    @multiarg
    def do_merge(self, source, target):
        """Merge source branch into target"""
        self.stdout.write('merge {} -> {}\n'.format(source, target))
        raise NotImplementedError

    def complete_merge(self, text, line, begidx, endidx):
        return self._complete_branches(text)

    @multiarg
    def do_push(self, branch):
        """Simultate push event to specified branch"""
        push_handler = self.push_handler_factory(self.config, branch, [], self.repo_manager)
        if self.forward:
            push_handler.logger.addHandler(self.get_logger_handler())
        push_handler.handle()

    def complete_push(self, text, line, begidx, endidx):
        return self._complete_branches(text)
