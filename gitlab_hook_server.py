import json
import asyncio
import argparse

from aiohttp import web

from push_handler import PushHandler
from config import Config, YamlFileConfigSource


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
    parser = argparse.ArgumentParser(description='gitlab hook server')
    parser.add_argument('-H', '--host', type=str, default='*', help='Listen host')
    parser.add_argument('-p', '--port', type=str, default='1234', help='Listen port')
    parser.add_argument('-c', '--config', type=str, help='Config file')
    args = parser.parse_args()
    run(args.host, args.port, args.config)
