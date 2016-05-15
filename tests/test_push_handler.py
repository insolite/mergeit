import os.path
import shutil
from unittest import TestCase
from unittest.mock import Mock, ANY, patch

from git import Repo

from push_handler import PushHandler, DEFAULT_REMOTE
from config import Config
from tests.common import MergeitTest


REPO_NAME = 'test_repo'
WORKSPACE = 'fixtures'


class PushHandlerTest(MergeitTest):

    def setUp(self):
        super().setUp()
        if os.path.exists(WORKSPACE):
            shutil.rmtree(WORKSPACE)
        self.repo = Repo.init(self.get_path())
        self.remote_repo = Repo.init(self.get_path() + '_remote', bare=True)
        self.repo.create_remote(DEFAULT_REMOTE, self.remote_repo.working_dir)
        self.commit_new_file('test.txt')
        self.repo.git.checkout('-b', 'develop')
        self.repo.remote().push(self.repo.active_branch.name)
        self.repo.git.checkout('master')
        commits = [{"id": "ffffff",
                    "message": "Test commit message\\n",
                    "timestamp": "2016-01-01T00:00:00+00:00",
                    "url": "http://localhost/test/test_repo/commit/ffffff",
                    "author": {"name": "test",
                               "email": "test@localhost"}}]
        self.config_source_mock = Mock()
        self.config_controller = Config(self.config_source_mock)
        self.configure({})
        self.push_handler = PushHandler(self.config_controller, REPO_NAME, 'master', 'git@localhost:test/{}.git'.format(REPO_NAME), commits)

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(WORKSPACE)

    def commit_new_file(self, name):
        with open(os.path.join(self.get_path(), name), 'w') as f:
            f.write('test data')
        self.repo.git.add(name)
        self.repo.git.commit('-m', '"Test commit message"')
        self.repo.remote().push(self.repo.active_branch.name)

    def get_path(self):
        return os.path.join(WORKSPACE, REPO_NAME)

    def configure(self, data):
        self.config_controller.data = dict(merge_workspace=WORKSPACE, **data)

    def test_fresh_checkout(self):
        # self.configure({})

        self.push_handler.fresh_checkout('develop')

        self.assertEqual(self.repo.active_branch.name, 'develop')

    @patch('push_handler.import_module')
    def test_merge_pair(self, import_mock):
        # self.configure({})
        filename = 'test2.txt'
        source_branch = 'master'
        target_branch = 'develop'
        self.repo.git.checkout(source_branch)
        self.commit_new_file(filename)
        test_filter_class = Mock()
        test_hook_class = Mock()
        test_filter = test_filter_class()
        test_hook = test_hook_class()
        test_filter.run.return_value = target_branch
        test_hook().run.return_value = target_branch
        test_filter_module = 'test_filter'
        test_hook_module = 'test_hook'
        self.push_handler.filters = {test_filter_module: test_filter}
        self.push_handler.hooks = {test_hook_module: test_hook}
        import_mock(test_filter_module).return_value = test_filter_class
        import_mock(test_hook_module).return_value = test_hook_class

        self.push_handler.merge_pair(source_branch, target_branch, [test_filter_module], [test_hook_module])

        self.repo.remote().fetch()
        self.repo.git.checkout(target_branch)
        self.repo.git.reset('--hard', '{}/{}'.format(self.repo.remote().name, target_branch))
        self.repo.git.clean('-df')
        self.assertTrue(os.path.exists(os.path.join(self.get_path(), filename)))
        test_filter.run.assert_called_once_with(ANY, source_branch, target_branch) # TODO: ANY - regexp match
        test_hook.run.assert_called_once_with(source_branch, target_branch, False)

    @patch('push_handler.PushHandler.merge_pair')
    def test_handle(self, merge_pair_mock):
        source_branch = 'master'
        target_branch = 'develop'
        self.configure({'dependencies': {'^{}$'.format(source_branch): {'targets': [target_branch]}}})

        self.push_handler.handle()

        merge_pair_mock.assert_called_once_with(ANY, target_branch, [], []) # FIXME: pass filters and hooks

    # @patch('push_handler.PushHandler.merge_pair')
    def test_get_branches_local(self):
        #

        branches = self.push_handler.get_branches(remote=False)

        self.assertSetEqual(set(branches), {'master', 'develop'})

    # @patch('push_handler.PushHandler.merge_pair')
    def test_get_branches_remote(self):
        #

        branches = self.push_handler.get_branches(remote=True)

        self.assertSetEqual(set(branches), {'master', 'develop'})
