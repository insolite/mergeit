import os.path
import shutil
from unittest.mock import MagicMock, ANY, patch
from importlib import import_module

from git import Repo

from core import push_handler
from core.push_handler import PushHandler, DEFAULT_REMOTE
from core.config.config import Config
from tests.common import MergeitTest


REPO_NAME = 'test_repo'
WORKSPACE = 'fixtures'


class PushHandlerTest(MergeitTest):

    def setUp(self):
        super().setUp()
        self.clean_workspace()
        self.repo = Repo.init(self.get_path())
        self.remote_repo = Repo.init(self.get_path() + '_remote', bare=True)
        self.repo.create_remote(DEFAULT_REMOTE, self.remote_repo.working_dir)
        self.commit_new_file('test.txt', 'test data')
        self.repo.git.checkout('-b', 'develop')
        self.repo.remote().push(self.repo.active_branch.name)
        self.repo.git.checkout('master')
        commits = [{"id": "ffffff",
                    "message": "Test commit message\\n",
                    "timestamp": "2016-01-01T00:00:00+00:00",
                    "url": "http://localhost/test/test_repo/commit/ffffff",
                    "author": {"name": "test",
                               "email": "test@localhost"}}]
        self.config_source_mock = MagicMock()
        self.config_controller = Config(self.config_source_mock)
        self.configure({})
        self.push_handler = PushHandler(self.config_controller, REPO_NAME, 'master', 'git@localhost:test/{}.git'.format(REPO_NAME), commits)

    def tearDown(self):
        super().tearDown()
        self.clean_workspace()

    def clean_workspace(self):
        if os.path.exists(WORKSPACE):
            shutil.rmtree(WORKSPACE)

    def commit_new_file(self, name, data):
        with open(os.path.join(self.get_path(), name), 'w') as f:
            f.write(data)
        self.repo.git.add(name)
        self.repo.git.commit('-m', '"Test commit message"')
        self.repo.remote().push(self.repo.active_branch.name)

    def get_path(self):
        return os.path.join(WORKSPACE, REPO_NAME)

    def configure(self, data):
        self.config_controller.data = dict(merge_workspace=WORKSPACE, **data)

    def test_get_repo__existing(self):
        path = self.get_path()
        self.push_handler.get_path = MagicMock(return_value=path)

        with patch.object(push_handler, 'Repo') as RepoMock:
            repo = self.push_handler.get_repo()

        RepoMock.assert_called_once_with(path)
        self.push_handler.get_path.assert_called_once_with()
        self.assertEqual(repo, RepoMock(path))

    def test_get_repo__clone(self):
        expected_repo = MagicMock()
        path = 'not-existing'
        self.push_handler.get_path = MagicMock(return_value=path)

        with patch.object(push_handler, 'Repo') as RepoMock:
            RepoMock.clone_from = MagicMock(return_value=expected_repo)
            repo = self.push_handler.get_repo()

        RepoMock.clone_from.assert_called_once_with(self.push_handler.uri, path)
        self.push_handler.get_path.assert_called_once_with()
        self.assertEqual(repo, expected_repo)

    def test_init_runners(self):
        with open(os.path.join(WORKSPACE, '__init__.py'), 'w') as f:
            f.write('')
        # Filter
        filter_module_name = 'test_filter'
        filter_class_name = 'TestFilter'
        with open(os.path.join(WORKSPACE, '{}.py').format(filter_module_name), 'w') as f:
            f.write('from core.runner import Filter\n'
                    'class {}(Filter): pass'.format(filter_class_name))

        filter_data = {'module': '{}.{}.{}'.format(WORKSPACE, filter_module_name, filter_class_name)}
        filter_extra = {'extra': 42}
        filter_data.update(filter_extra)
        # Hook
        hook_module_name = 'test_hook'
        hook_class_name = 'TestHook'
        with open(os.path.join(WORKSPACE, '{}.py').format(hook_module_name), 'w') as f:
            f.write('from core.runner import Hook\n'
                    'class {}(Hook): pass'.format(hook_class_name))
        hook_data = {'module': '{}.{}.{}'.format(WORKSPACE, hook_module_name, hook_class_name)}
        hook_extra = {'foo': 24}
        hook_data.update(hook_extra)
        # Configure
        self.configure({'filters_def': {filter_module_name: filter_data},
                        'hooks_def': {hook_module_name: hook_data}})
        # Import
        filter_module = import_module('{}.{}'.format(WORKSPACE, filter_module_name))
        filter_class = getattr(filter_module, filter_class_name)
        hook_module = import_module('{}.{}'.format(WORKSPACE, hook_module_name))
        hook_class = getattr(hook_module, hook_class_name)

        self.push_handler.init_runners()

        filter_ = self.push_handler.filters[filter_module_name]
        hook = self.push_handler.hooks[hook_module_name]
        self.assertIsInstance(filter_, filter_class)
        self.assertIsInstance(hook, hook_class)
        self.assertEqual(filter_.push_handler, self.push_handler)
        self.assertEqual(hook.push_handler, self.push_handler)
        self.assertEqual(filter_.config, filter_extra)
        self.assertEqual(hook.config, hook_extra)

    def test_fresh_checkout__success(self):
        # self.configure({})

        self.push_handler.fresh_checkout('develop')

        self.assertEqual(self.repo.active_branch.name, 'develop')

    def test_fresh_checkout__git_error(self):
        # self.configure({})
        branch = 'not-existing'
        base_commit = self.repo.active_branch.commit

        self.push_handler.fresh_checkout(branch)

        self.assertEqual(self.repo.active_branch.name, branch)
        self.assertEqual(self.repo.active_branch.commit, base_commit)

    def test_merge__no_conflict(self):
        # self.configure({})
        filename = 'test2.txt'
        source_branch = 'master'
        target_branch = 'develop'
        self.repo.git.checkout(source_branch)
        self.commit_new_file(filename, 'test data')

        conflict = self.push_handler.merge(target_branch)

        # self.repo.remote().fetch()
        # self.repo.git.checkout(target_branch)
        # self.repo.git.reset('--hard', '{}/{}'.format(self.repo.remote().name, target_branch))
        # self.repo.git.clean('-df')
        self.assertTrue(os.path.exists(os.path.join(self.get_path(), filename)))
        self.assertFalse(conflict)

    def test_merge__conflict(self):
        # self.configure({})
        filename = 'test2.txt'
        source_branch = 'master'
        target_branch = 'develop'
        self.repo.git.checkout(source_branch)
        self.commit_new_file(filename, 'test data')
        self.repo.git.checkout(target_branch)
        self.commit_new_file(filename, 'test data 2')
        self.repo.git.checkout(source_branch)
        self.commit_new_file(filename, 'test data 1')

        conflict = self.push_handler.merge(target_branch)

        self.assertTrue(conflict)

    @patch('core.push_handler.import_module')
    def test_process_merge_pair__merge(self, import_mock):
        # self.configure({})
        source_branch = 'master'
        target_branch = 'develop'
        test_filter_class = MagicMock()
        test_hook_class = MagicMock()
        test_filter = test_filter_class()
        test_hook = test_hook_class()
        test_filter.run.return_value = target_branch
        test_hook.run.return_value = target_branch
        test_filter_module = 'test_filter'
        test_hook_module = 'test_hook'
        self.push_handler.filters = {test_filter_module: test_filter}
        self.push_handler.hooks = {test_hook_module: test_hook}
        import_mock(test_filter_module).return_value = test_filter_class
        import_mock(test_hook_module).return_value = test_hook_class
        conflict = MagicMock()
        self.push_handler.merge = MagicMock(return_value=conflict)

        self.push_handler.process_merge_pair(source_branch, target_branch, [test_filter_module], [test_hook_module])

        self.push_handler.merge.assert_called_once_with(target_branch)
        test_filter.run.assert_called_once_with(ANY, source_branch, target_branch) # TODO: ANY - regexp match
        test_hook.run.assert_called_once_with(source_branch, target_branch, conflict)

    @patch('core.push_handler.import_module')
    def test_process_merge_pair__merge_cancel(self, import_mock):
        # self.configure({})
        source_branch = 'master'
        target_branch = 'develop'
        test_filter_class = MagicMock()
        test_hook_class = MagicMock()
        test_filter = test_filter_class()
        test_hook = test_hook_class()
        test_filter.run.return_value = None
        test_hook.run.return_value = target_branch
        test_filter_module = 'test_filter'
        test_hook_module = 'test_hook'
        self.push_handler.filters = {test_filter_module: test_filter}
        self.push_handler.hooks = {test_hook_module: test_hook}
        import_mock(test_filter_module).return_value = test_filter_class
        import_mock(test_hook_module).return_value = test_hook_class
        self.push_handler.merge = MagicMock()

        self.push_handler.process_merge_pair(source_branch, target_branch, [test_filter_module], [test_hook_module])

        self.push_handler.merge.assert_not_called()
        test_filter.run.assert_called_once_with(ANY, source_branch, target_branch) # TODO: ANY - regexp match
        test_hook.run.assert_not_called()

    def test_handle(self):
        source_branch = 'master'
        target_branch = 'develop'
        self.configure({'dependencies': {'^{}$'.format(source_branch): {'targets': [target_branch]}}})
        self.push_handler.process_merge_pair = MagicMock()

        self.push_handler.handle()

        self.push_handler.process_merge_pair.assert_called_once_with(ANY, target_branch, [], []) # FIXME: pass filters and hooks

    def test_handle__variables(self):
        source_version = '3\\.0'
        target_version = '4\\.0'
        source_branch = 'v{source_version}'
        target_branch = 'v{target_version}'
        self.push_handler.branch = 'v3.0'
        self.configure({'dependencies': {'^{}$'.format(source_branch): {'targets': [target_branch]}},
                        'variables': {'source_version': source_version,
                                      'target_version': target_version}})
        self.push_handler.process_merge_pair = MagicMock()

        self.push_handler.handle()

        self.push_handler.process_merge_pair.assert_called_once_with(ANY, target_branch.format(target_version=target_version), [], []) # FIXME: pass filters and hooks

    # @patch('push_handler.PushHandler.merge_pair')
    def test_get_branches__local(self):
        #

        branches = self.push_handler.get_branches(remote=False)

        self.assertSetEqual(set(branches), {'master', 'develop'})

    # @patch('push_handler.PushHandler.merge_pair')
    def test_get_branches__remote(self):
        #

        branches = self.push_handler.get_branches(remote=True)

        self.assertSetEqual(set(branches), {'master', 'develop'})
