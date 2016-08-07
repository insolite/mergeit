import json
import asyncio
from unittest import TestCase
from unittest.mock import MagicMock, patch, ANY

from runner import Runner, Filter, Hook


class RunnerTest(TestCase):

    def setUp(self):
        super().setUp()
        self.runner = Runner(MagicMock())

    def test_run(self):
        self.assertRaises(NotImplementedError, self.runner.run)


class FilterTest(TestCase):

    def setUp(self):
        super().setUp()
        self.runner = Filter(MagicMock())

    def test_run(self):
        self.assertRaises(NotImplementedError, self.runner.run, MagicMock(), MagicMock(), MagicMock())


class HookTest(TestCase):

    def setUp(self):
        super().setUp()
        self.runner = Hook(MagicMock())

    def test_run(self):
        self.assertRaises(NotImplementedError, self.runner.run, MagicMock(), MagicMock(), MagicMock())
