import json
import os.path
import shutil
import asyncio
from unittest import TestCase
from unittest.mock import Mock, ANY, patch

from git import Repo
from aiohttp import web

from push_handler import PushHandler, DEFAULT_REMOTE
from gitlab_hook_server import push
from config import Config
from tests.common import get_mock_coro


class GitlabHookServerTest(TestCase):

    def setUp(self):
        super().setUp()
        # TODO: another way of mocking get_event_loop
        self.loop = asyncio.get_event_loop()

    @patch('gitlab_hook_server.asyncio.get_event_loop')
    @patch('gitlab_hook_server.PushHandler')
    def test_push(self, push_handler_mock, get_event_loop_mock):
        loop_mock = Mock()
        request_mock = Mock()
        config_mock = Mock()
        get_event_loop_mock.return_value = loop_mock
        # TODO: add real request data
        request_mock.payload.read = get_mock_coro(json.dumps(
            {'repository': {'name': 'test',
                            'git_ssh_url': 'http://localhost'},
             'ref': 'refs/heads/master',
             'commits': [{}]}).encode())

        response = self.loop.run_until_complete(push(request_mock, config_mock))

        self.assertIsInstance(response, web.Response)
        self.assertEqual(response.status, 200)
        config_mock.reload.assert_called_once_with()
        # TODO: PushHandler.__init__ call assertion?
        loop_mock.call_soon.assert_called_once_with(push_handler_mock().handle)