import json
import asyncio
import unittest
from unittest.mock import MagicMock

from logging_extras import init_logging


class ResponseMock(MagicMock):

    def __init__(self, data, status_code=200, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = data if isinstance(data, str) else json.dumps(data)
        self.status_code = status_code


class RunnerTest(unittest.TestCase):

    def setUp(self):
        self.push_handler_mock = MagicMock()


class MergeitTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        init_logging('../logs/gitlab_hook_server.log')


def get_mock_coro(return_value):
    @asyncio.coroutine
    def mock_coro(*args, **kwargs):
        return return_value
    return MagicMock(wraps=mock_coro)