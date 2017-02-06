import asyncio
import json
import logging.config

from aiohttp import web
from structlog import get_logger
import telnetlib3
from telnetlib3 import TelnetServer
from telnetlib3.telsh import TelnetShellStream
import configargparse

from mergeit.core.config.config import Config
from mergeit.core.config.yaml_config_source import YamlFileConfigSource
from mergeit.core.push_handler import PushHandler
from mergeit.core.repo_manager import RepoManager
from mergeit.core.shell import MergeitShell
from mergeit.overrides.cmd_telsh import CmdTelsh
from mergeit.scripts.common import init_logging


@asyncio.coroutine
def gitlab_push(request, config):
    data = json.loads((yield from request.content.read()).decode())
    branch = data['ref'].split('refs/heads/')[1]
    config.reload()
    repo_manager = RepoManager(config['name'],
                               config['uri'],
                               config['merge_workspace'])
    handler = PushHandler(config,
                          branch,
                          data['commits'],
                          repo_manager)
    # re.match(r'(.+?:\/\/.+?)\/', data['repository']['homepage']).group(1),
    loop = asyncio.get_event_loop()
    # Close connection first, then handle
    # (if gitlab can not get response for too long it is repeating request)
    loop.call_soon(handler.handle)
    return web.Response()


def run(host, port, shell_host, shell_port, project_config, log,
        application_factory=web.Application,
        config_factory=Config,
        config_source_factory=YamlFileConfigSource,
        push_handler_factory=PushHandler,
        repo_manager_factory=RepoManager,
        cmd_factory=MergeitShell,
        telnet_shell_factory=CmdTelsh,
        telnet_server_factory=TelnetServer):
    logger = get_logger()
    loop = asyncio.get_event_loop()
    app = application_factory()
    config = config_factory(config_source_factory(project_config))
    init_logging(log, config.get('name'))
    app.router.add_route('POST', '/push', lambda request: gitlab_push(request, config))
    logger.info('application_start')
    loop.run_until_complete(loop.create_server(app.make_handler(), host, port))
    shell = cmd_factory(config=config,
                        push_handler_factory=push_handler_factory,
                        repo_manager_factory=repo_manager_factory,
                        forward=True)
    shell_factory = (lambda server, stream=TelnetShellStream, log=logging:
                     telnet_shell_factory(server, stream, log, cmd=shell))
    loop.run_until_complete(
        loop.create_server(lambda: telnet_server_factory(log=logging.getLogger(telnetlib3.__name__), shell=shell_factory),
                           shell_host, shell_port)
    )
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('application_interrupt')


def main():
    parser = configargparse.ArgParser(description='mergeit hook server')
    parser.add_argument('-sc', '--server-config', is_config_file=True, help='Server config')
    parser.add_argument('-H', '--host', type=str, default='*', help='Listen host')
    parser.add_argument('-p', '--port', type=int, default=1234, help='Listen port')
    parser.add_argument('-sh', '--shell-host', type=str, default='*', help='Shell listen host')
    parser.add_argument('-sp', '--shell-port', type=int, default=1235, help='Shell listen port')
    parser.add_argument('-c', '--config', type=str, help='Config file')
    parser.add_argument('-l', '--log', type=str, default='/var/log/mergeit', help='Logs dir')
    args = parser.parse_args()
    run(args.host, args.port, args.shell_host, args.shell_port, args.config, args.log)


if __name__ == '__main__':
    main()
