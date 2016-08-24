import sys
import os.path
import json
import asyncio
import argparse
import logging.config

from aiohttp import web
from context_logging import uncaught_exception, getLogger

from mergeit.core.push_handler import PushHandler
from mergeit.core.config.config import Config
from mergeit.core.config.yaml_config_source import YamlFileConfigSource


LOGGING_FORMAT = '%(asctime)s %(levelname)-7s %(message)-20s %(context)s'


def init_logging(log_dir):
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,

        'formatters': {
            'standard': {
                'format': LOGGING_FORMAT,
            },
            'colored': {
                '()': 'context_logging.ColoredFormatter',
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
                'filename': os.path.join(log_dir, 'server.log'),
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


@asyncio.coroutine
def push(request, config):
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
    logger = getLogger(__name__)
    loop = asyncio.get_event_loop()
    app = web.Application()
    config = Config(YamlFileConfigSource(project_config))
    app.router.add_route('POST', '/push', lambda request: push(request, config))
    logger.info('application_start')
    loop.run_until_complete(loop.create_server(app.make_handler(), host, port))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('application_interrupt')


def main():
    parser = argparse.ArgumentParser(description='gitlab hook server')
    parser.add_argument('-H', '--host', type=str, default='*', help='Listen host')
    parser.add_argument('-p', '--port', type=str, default='1234', help='Listen port')
    parser.add_argument('-c', '--config', type=str, help='Config file')
    parser.add_argument('-l', '--log', type=str, default='/var/log/mergeit', help='Logs dir')
    args = parser.parse_args()
    init_logging(args.log)
    run(args.host, args.port, args.config)


if __name__ == '__main__':
    main()