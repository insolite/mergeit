import unittest
from unittest.mock import Mock


class FilterTest(unittest.TestCase):

    def setUp(self):
        self.push_handler_mock = Mock()
