import sys
import os.path
import json
import asyncio
import argparse
import logging.config

from aiohttp import web
from structlog import get_logger
import structlog

from mergeit.logging_extras import ProcessorFormatter, event_dict_to_message
from mergeit.core.push_handler import PushHandler
from mergeit.core.config.config import Config
from mergeit.core.config.yaml_config_source import YamlFileConfigSource


def uncaught_exception(exctype, value, tb):
    logger = get_logger()
    try:
        raise value
    except:
        logger.critical('uncaught_exception', name=exctype.__name__, args=value.args, exc_info=True)


def init_logging(log_dir):
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
                'filename': os.path.join(log_dir, 'server.log'),
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


@asyncio.coroutine
def gitlab_push(request, config):
    data = json.loads((yield from request.content.read()).decode())
    project_name = data['repository']['name']
    branch = data['ref'].split('refs/heads/')[1]
    config.reload()
    handler = PushHandler(config,
                          project_name,
                          branch,
                          data['repository']['git_ssh_url'],
                          data['commits'])
    # re.match(r'(.+?:\/\/.+?)\/', data['repository']['homepage']).group(1),
    loop = asyncio.get_event_loop()
    # Close connection first, then handle
    # (if gitlab can not get response for too long it is repeating request)
    loop.call_soon(handler.handle)
    return web.Response()


def run(host, port, project_config):
    logger = get_logger()
    loop = asyncio.get_event_loop()
    app = web.Application()
    config = Config(YamlFileConfigSource(project_config))
    app.router.add_route('POST', '/push', lambda request: gitlab_push(request, config))
    logger.info('application_start')
    loop.run_until_complete(loop.create_server(app.make_handler(), host, port))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('application_interrupt')


def main():
    parser = argparse.ArgumentParser(description='mergeit hook server')
    parser.add_argument('-H', '--host', type=str, default='*', help='Listen host')
    parser.add_argument('-p', '--port', type=str, default='1234', help='Listen port')
    parser.add_argument('-c', '--config', type=str, help='Config file')
    parser.add_argument('-l', '--log', type=str, default='/var/log/mergeit', help='Logs dir')
    args = parser.parse_args()
    init_logging(args.log)
    run(args.host, args.port, args.config)


if __name__ == '__main__':
    main()