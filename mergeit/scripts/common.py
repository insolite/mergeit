import os.path
import sys
import logging.config

import structlog
from structlog import get_logger

from mergeit.overrides.logging_extras import ProcessorFormatter, event_dict_to_message


def uncaught_exception(exctype, value, tb):
    logger = get_logger()
    try:
        raise value
    except:
        logger.critical('uncaught_exception', name=exctype.__name__, args=value.args, exc_info=True)


def init_logging(log_dir, name):
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'plain': {
                '()': ProcessorFormatter,
                'processor': structlog.dev.ConsoleRenderer(), # TODO: ConsoleRenderer without coloring
            },
            'colored': {
                '()': ProcessorFormatter,
                'processor': structlog.dev.ConsoleRenderer(),
            },
        },
        'handlers': {
            'default': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'colored',
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.WatchedFileHandler',
                'filename': os.path.join(log_dir, '{}.log'.format(name)),
                'formatter': 'plain',
            },
        },
        'loggers': {
            '': {
                'handlers': ['default', 'file'],
                'level': 'DEBUG',
                'propagate': True,
            },
            'asyncio': {
                'propagate': False,
            },
            'telnetlib3': {
                'propagate': False,
            },
        }
    })
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt='%Y-%m-%d %H:%M:%S'),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            event_dict_to_message,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    sys.excepthook = uncaught_exception
