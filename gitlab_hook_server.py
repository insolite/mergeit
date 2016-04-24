import json
import asyncio

from aiohttp import web

from push_handler import PushHandler
from config import Config, YamlFileConfigSource


HOOK_HOST = '0.0.0.0'
HOOK_PORT = 1234
PROJECT_CONFIG = 'config_sample.yaml'


@asyncio.coroutine
def push(request, config):
    data = json.loads((yield from request.payload.read()).decode())
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
    loop = asyncio.get_event_loop()
    app = web.Application()
    config = Config(YamlFileConfigSource(project_config))
    app.router.add_route('POST', '/push', lambda request: push(request, config))
    loop.run_until_complete(loop.create_server(app.make_handler(), host, port))
    loop.run_forever()


if __name__ == '__main__':
    # TODO: argparse
    run(HOOK_HOST, HOOK_PORT, PROJECT_CONFIG)
