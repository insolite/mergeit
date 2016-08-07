import logging.config
import json
import datetime
import sys
from json.encoder import JSONEncoder


LOGGING_FORMAT = '%(asctime)s %(levelname)-7s %(message)-20s %(context)s'


def uncaught_exception(exctype, value, tb):
    logger = ContextAdapter(logging.getLogger(__name__), {})
    try:
        raise value
    except:
        logger.critical('uncaught_exception', name=exctype.__name__, exc_info=True)


def init_logging(filename='logs/gitlab_hook_server.log'):
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,

        'formatters': {
            'standard': {
                'format': LOGGING_FORMAT,
            },
            'colored': {
                '()': 'logging_extras.ColoredFormatter',
                'format': LOGGING_FORMAT,
            },
        },
        'handlers': {
            'default': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'colored',
            },
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'colored',
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.WatchedFileHandler',
                'filename': filename,
                'formatter': 'standard',
            },
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': True,
            },
            'asyncio': {
                'propagate': False,
            },
        }
    })
    sys.excepthook = uncaught_exception


class ColoredFormatter(logging.Formatter):

    COLOR_RESET = '\x1B[0m'
    COLOR_WHITE = '\x1B[01;1m'
    COLOR_RED = '\x1B[01;31m'
    COLOR_YELLOW = '\x1B[01;33m'
    COLOR_BRGREEN = '\x1B[01;32m'
    COLOR_MAGENTA = '\x1B[01;35m'

    def format(self, record):
        if not hasattr(record, 'context'):
            record.context = ''
        message = super().format(record)

        level_no = record.levelno
        if level_no >= logging.CRITICAL:
            color = self.COLOR_MAGENTA
        elif level_no >= logging.ERROR:
            color = self.COLOR_RED
        elif level_no >= logging.WARNING:
            color = self.COLOR_YELLOW
        elif level_no >= logging.INFO:
            color = self.COLOR_WHITE
        elif level_no >= logging.DEBUG:
            color = self.COLOR_BRGREEN
        else:
            color = self.COLOR_RESET

        message = color + message + self.COLOR_RESET

        return message


class CustomJsonEncoder(JSONEncoder):

    def default(self, o):
        if hasattr(o, '__json__'):
            return o.__json__()
        elif isinstance(o, datetime.datetime):
            return str(o)
        elif isinstance(o, datetime.timedelta):
            return str(o)
        elif isinstance(o, bytes):
            return str(o)
        try:
            return super().default(o)
        except TypeError:
            return str(o)


class ContextAdapter(logging.LoggerAdapter):

    EXTRA_KEY = 'extra'

    def process(self, msg, kwargs):
        extra_args = kwargs.copy()
        actual_args = {}
        for key in (self.EXTRA_KEY, 'exc_info', 'stack_info'):
            if key in kwargs:
                actual_args[key] = extra_args.pop(key)
        if self.EXTRA_KEY in actual_args:
            extra_args.update(actual_args[self.EXTRA_KEY])
        else:
            actual_args[self.EXTRA_KEY] = {}
        context_str = '{}'.format(
            ', '.join(['{}={}'.format(key, json.dumps(val, cls=CustomJsonEncoder))
                       for extra in (self.extra, extra_args)
                       for key, val in sorted(extra.items(),
                                              key=lambda x: x[0])]))
        actual_args[self.EXTRA_KEY]['context'] = context_str
        return msg, actual_args
