import os.path
import shutil
import asyncio
from unittest import TestCase
from unittest.mock import Mock, ANY

from git import Repo

from push_handler import PushHandler, DEFAULT_REMOTE
from config import Config


class GitlabHookServerTest(TestCase):

    def test_push(self):
        pass
