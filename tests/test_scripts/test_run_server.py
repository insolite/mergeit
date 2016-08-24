import asyncio
import json
from unittest import TestCase
from unittest.mock import MagicMock, patch, ANY

from aiohttp import web
from asynctest.mock import CoroutineMock

from mergeit.scripts import run_server


class GitlabHookServerTest(TestCase):

    def setUp(self):
        super().setUp()
        # TODO: another way of mocking get_event_loop
        self.loop = asyncio.get_event_loop()

    def test_gitlab_push(self):
        loop_mock = MagicMock()
        request_mock = MagicMock()
        config_mock = MagicMock()
        project_name = 'test'
        branch = 'master'
        git_ssh_url = 'http://localhost'
        commits = [{}]
        # TODO: add real request data
        request_mock.content.read = CoroutineMock(return_value=json.dumps(
            {'repository': {'name': project_name,
                            'git_ssh_url': git_ssh_url},
             'ref': 'refs/heads/{}'.format(branch),
             'commits': commits}).encode())

        with patch.object(run_server.asyncio, 'get_event_loop', MagicMock(return_value=loop_mock)) as get_event_loop_mock,\
             patch.object(run_server, 'PushHandler') as PushHandlerMock:
                 response = self.loop.run_until_complete(
                     run_server.gitlab_push(request_mock, config_mock))

        get_event_loop_mock.assert_called_once_with()
        self.assertIsInstance(response, web.Response)
        self.assertEqual(response.status, 200)
        config_mock.reload.assert_called_once_with()
        PushHandlerMock.assert_called_once_with(config_mock,
                                                project_name,
                                                branch,
                                                git_ssh_url,
                                                commits)
        loop_mock.call_soon.assert_called_once_with(PushHandlerMock().handle)

    def test_run(self):
        host = MagicMock()
        port = MagicMock()
        config_file = MagicMock()
        loop = MagicMock()
        app = MagicMock()
        config = MagicMock()
        config_source = MagicMock()
        app_handler = MagicMock()
        server = MagicMock()
        app.make_handler = MagicMock(return_value=app_handler)
        loop.create_server = MagicMock(return_value=server)

        with patch.object(run_server.asyncio, 'get_event_loop', MagicMock(return_value=loop)) as get_event_loop_mock,\
             patch.object(run_server.web, 'Application', MagicMock(return_value=app)) as ApplicationMock,\
             patch.object(run_server, 'Config', MagicMock(return_value=config)) as ConfigMock,\
             patch.object(run_server, 'YamlFileConfigSource', MagicMock(return_value=config_source)) as YamlFileConfigSourceMock:
            run_server.run(host, port, config_file)

        get_event_loop_mock.assert_called_once_with()
        ApplicationMock.assert_called_once_with()
        YamlFileConfigSourceMock.assert_called_once_with(config_file)
        ConfigMock.assert_called_once_with(config_source)
        app.router.add_route.assert_called_once_with('POST', '/push', ANY) # TODO: mock lambda
        app.make_handler.assert_called_once_with()
        loop.create_server.assert_called_once_with(app_handler, host, port)
        loop.run_until_complete.assert_called_once_with(server)
        loop.run_forever.assert_called_once_with()

    def test_run__interrupt(self):
        host = MagicMock()
        port = MagicMock()
        config_file = MagicMock()
        loop = MagicMock()
        app = MagicMock()
        config = MagicMock()
        config_source = MagicMock()
        app_handler = MagicMock()
        server = MagicMock()
        app.make_handler = MagicMock(return_value=app_handler)
        loop.create_server = MagicMock(return_value=server)
        loop.run_forever = MagicMock(side_effect=KeyboardInterrupt)

        with patch.object(run_server.asyncio, 'get_event_loop', MagicMock(return_value=loop)) as get_event_loop_mock,\
             patch.object(run_server.web, 'Application', MagicMock(return_value=app)) as ApplicationMock,\
             patch.object(run_server, 'Config', MagicMock(return_value=config)) as ConfigMock,\
             patch.object(run_server, 'YamlFileConfigSource', MagicMock(return_value=config_source)) as YamlFileConfigSourceMock:
            run_server.run(host, port, config_file)

        get_event_loop_mock.assert_called_once_with()
        ApplicationMock.assert_called_once_with()
        YamlFileConfigSourceMock.assert_called_once_with(config_file)
        ConfigMock.assert_called_once_with(config_source)
        app.router.add_route.assert_called_once_with('POST', '/push', ANY) # TODO: mock lambda
        app.make_handler.assert_called_once_with()
        loop.create_server.assert_called_once_with(app_handler, host, port)
        loop.run_until_complete.assert_called_once_with(server)
        loop.run_forever.assert_called_once_with()

    def test_main(self):
        args = MagicMock()
        parser = MagicMock()
        parser.parse_args = MagicMock(return_value=args)

        with patch.object(run_server, 'init_logging') as init_logging_mock,\
             patch.object(run_server, 'run') as run_mock,\
             patch.object(run_server.argparse, 'ArgumentParser', MagicMock(return_value=parser)) as ArgumentParserMock:
            run_server.main()

        ArgumentParserMock.assert_called_once_with(description=ANY)
        parser.parse_args.assert_called_once_with()
        init_logging_mock.assert_called_once_with(args.log)
        run_mock.assert_called_once_with(args.host, args.port, args.config)
