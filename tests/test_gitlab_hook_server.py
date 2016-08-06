import json
import asyncio
from unittest import TestCase
from unittest.mock import MagicMock, patch

from aiohttp import web
from asynctest.mock import CoroutineMock

from gitlab_hook_server import push
import gitlab_hook_server


class GitlabHookServerTest(TestCase):

    def setUp(self):
        super().setUp()
        # TODO: another way of mocking get_event_loop
        self.loop = asyncio.get_event_loop()

    def test_push(self):
        loop_mock = MagicMock()
        request_mock = MagicMock()
        config_mock = MagicMock()
        project_name = 'test'
        branch = 'master'
        git_ssh_url = 'http://localhost'
        commits = [{}]
        # TODO: add real request data
        request_mock.payload.read = CoroutineMock(return_value=json.dumps(
            {'repository': {'name': project_name,
                            'git_ssh_url': git_ssh_url},
             'ref': 'refs/heads/{}'.format(branch),
             'commits': commits}).encode())

        with patch.object(gitlab_hook_server, 'asyncio') as asyncio_mock:
            with patch.object(gitlab_hook_server, 'PushHandler') as PushHandlerMock:
                asyncio_mock.get_event_loop = MagicMock(return_value=loop_mock)
                response = self.loop.run_until_complete(push(request_mock, config_mock))

        self.assertIsInstance(response, web.Response)
        self.assertEqual(response.status, 200)
        config_mock.reload.assert_called_once_with()
        PushHandlerMock.assert_called_once_with(config_mock,
                                                project_name,
                                                branch,
                                                git_ssh_url,
                                                commits)
        loop_mock.call_soon.assert_called_once_with(PushHandlerMock().handle)