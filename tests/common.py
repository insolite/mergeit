import asyncio
import unittest
from unittest.mock import Mock


class FilterTest(unittest.TestCase):

    def setUp(self):
        self.push_handler_mock = Mock()


def get_mock_coro(return_value):
    @asyncio.coroutine
    def mock_coro(*args, **kwargs):
        return return_value
    return Mock(wraps=mock_coro)