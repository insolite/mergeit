import asyncio
import json
from unittest import TestCase
from unittest.mock import MagicMock, patch, ANY, call

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
                                                branch,
                                                commits)
        loop_mock.call_soon.assert_called_once_with(PushHandlerMock().handle)

    def test_run(self):
        host = MagicMock()
        port = MagicMock()
        shell_host = MagicMock()
        shell_port = MagicMock()
        config_file = MagicMock()
        loop = MagicMock()
        app = MagicMock()
        app_factory = MagicMock(return_value=app)
        shell = MagicMock()
        push_handler_factory = MagicMock()
        cmd_factory = MagicMock(return_value=shell)
        telnet_shell_factory = MagicMock()
        telnet_server_factory = MagicMock()
        config = MagicMock()
        config_factory = MagicMock(return_value=config)
        config_source = MagicMock()
        config_source_factory = MagicMock(return_value=config_source)
        app_handler = MagicMock()
        server = MagicMock()
        telnet_server = MagicMock()
        app.make_handler = MagicMock(return_value=app_handler)
        loop.create_server = MagicMock(side_effect=[server, telnet_server])
        loop.run_forever = MagicMock()

        with patch.object(run_server.asyncio, 'get_event_loop', MagicMock(return_value=loop)) as get_event_loop_mock:
            run_server.run(host, port, shell_host, shell_port, config_file,
                           application_factory=app_factory,
                           config_factory=config_factory,
                           config_source_factory=config_source_factory,
                           push_handler_factory=push_handler_factory,
                           cmd_factory=cmd_factory,
                           telnet_shell_factory=telnet_shell_factory,
                           telnet_server_factory=telnet_server_factory)

        get_event_loop_mock.assert_called_once_with()
        app_factory.assert_called_once_with()
        config_source_factory.assert_called_once_with(config_file)
        config_factory.assert_called_once_with(config_source)
        app.router.add_route.assert_called_once_with('POST', '/push', ANY) # TODO: mock lambda
        app.make_handler.assert_called_once_with()
        cmd_factory.assert_called_once_with(config=config, push_handler_factory=push_handler_factory, forward=True)
        loop.create_server.assert_has_calls([call(app_handler, host, port),
                                             call(ANY, shell_host, shell_port)], # TODO: ANY - server
                                            any_order=True)
        loop.run_until_complete.assert_has_calls([call(server),
                                                  call(telnet_server)],
                                                 any_order=True)
        loop.run_forever.assert_called_once_with()

    def test_run__interrupt(self):
        host = MagicMock()
        port = MagicMock()
        shell_host = MagicMock()
        shell_port = MagicMock()
        config_file = MagicMock()
        loop = MagicMock()
        app = MagicMock()
        app_factory = MagicMock(return_value=app)
        shell = MagicMock()
        push_handler_factory = MagicMock()
        cmd_factory = MagicMock(return_value=shell)
        telnet_shell_factory = MagicMock()
        telnet_server_factory = MagicMock()
        config = MagicMock()
        config_factory = MagicMock(return_value=config)
        config_source = MagicMock()
        config_source_factory = MagicMock(return_value=config_source)
        app_handler = MagicMock()
        server = MagicMock()
        telnet_server = MagicMock()
        app.make_handler = MagicMock(return_value=app_handler)
        loop.create_server = MagicMock(side_effect=[server, telnet_server])
        loop.run_forever = MagicMock(side_effect=KeyboardInterrupt)

        with patch.object(run_server.asyncio, 'get_event_loop', MagicMock(return_value=loop)) as get_event_loop_mock:
            run_server.run(host, port, shell_host, shell_port, config_file,
                           application_factory=app_factory,
                           config_factory=config_factory,
                           config_source_factory=config_source_factory,
                           push_handler_factory=push_handler_factory,
                           cmd_factory=cmd_factory,
                           telnet_shell_factory=telnet_shell_factory,
                           telnet_server_factory=telnet_server_factory)

        get_event_loop_mock.assert_called_once_with()
        app_factory.assert_called_once_with()
        config_source_factory.assert_called_once_with(config_file)
        config_factory.assert_called_once_with(config_source)
        app.router.add_route.assert_called_once_with('POST', '/push', ANY) # TODO: mock lambda
        app.make_handler.assert_called_once_with()
        cmd_factory.assert_called_once_with(config=config, push_handler_factory=push_handler_factory, forward=True)
        loop.create_server.assert_has_calls([call(app_handler, host, port),
                                             call(ANY, shell_host, shell_port)], # TODO: ANY - server
                                            any_order=True)
        loop.run_until_complete.assert_has_calls([call(server),
                                                  call(telnet_server)],
                                                 any_order=True)
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
        run_mock.assert_called_once_with(args.host, args.port, args.shell_host, args.shell_port, args.config)
