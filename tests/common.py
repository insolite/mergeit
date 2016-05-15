import asyncio
import unittest
from unittest.mock import Mock

from logging_extras import init_logging


class FilterTest(unittest.TestCase):

    def setUp(self):
        self.push_handler_mock = Mock()


class MergeitTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        init_logging('../logs/gitlab_hook_server.log')


def get_mock_coro(return_value):
    @asyncio.coroutine
    def mock_coro(*args, **kwargs):
        return return_value
    return Mock(wraps=mock_coro)