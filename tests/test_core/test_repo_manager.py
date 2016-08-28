import os.path
import shutil
from unittest.mock import MagicMock, ANY, patch

from git import Repo

from mergeit.core import repo_manager
from mergeit.core.push_handler import DEFAULT_REMOTE
from mergeit.core.repo_manager import RepoManager
from tests.common import MergeitTest


REPO_NAME = 'test_repo'
WORKSPACE = 'fixtures'


class RepoManagerTest(MergeitTest):

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
        self.uri = 'git@localhost:test/{}.git'.format(REPO_NAME)
        self.repo_manager = RepoManager(REPO_NAME, self.uri, WORKSPACE)

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

    def test_get_repo__existing(self):
        path = self.get_path()
        self.repo_manager.get_path = MagicMock(return_value=path)

        with patch.object(repo_manager, 'Repo') as RepoMock:
            repo = self.repo_manager.get_repo()

        RepoMock.assert_called_once_with(path)
        self.repo_manager.get_path.assert_called_once_with()
        self.assertEqual(repo, RepoMock(path))

    def test_get_repo__clone(self):
        expected_repo = MagicMock()
        path = 'not-existing'
        self.repo_manager.get_path = MagicMock(return_value=path)

        with patch.object(repo_manager, 'Repo') as RepoMock:
            RepoMock.clone_from = MagicMock(return_value=expected_repo)
            repo = self.repo_manager.get_repo()

        RepoMock.clone_from.assert_called_once_with(self.uri, path)
        self.repo_manager.get_path.assert_called_once_with()
        self.assertEqual(repo, expected_repo)

    def test_fresh_checkout__success(self):
        # self.configure({})
        self.repo_manager.fetch = MagicMock()

        self.repo_manager.fresh_checkout('develop', 'master')

        self.repo_manager.fetch.assert_called_once_with()
        self.assertEqual(self.repo.active_branch.name, 'develop')

    def test_fresh_checkout__git_error(self):
        # self.configure({})
        branch = 'not-existing'
        base_commit = self.repo.active_branch.commit
        self.repo_manager.fetch = MagicMock()

        self.repo_manager.fresh_checkout(branch, 'master')

        self.repo_manager.fetch.assert_called_once_with()
        self.assertEqual(self.repo.active_branch.name, branch)
        self.assertEqual(self.repo.active_branch.commit, base_commit)

    def test_merge__no_conflict(self):
        # self.configure({})
        filename = 'test2.txt'
        source_branch = 'master'
        target_branch = 'develop'
        self.repo.git.checkout(source_branch)
        self.commit_new_file(filename, 'test data')

        conflict = self.repo_manager.merge(source_branch, target_branch)

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

        conflict = self.repo_manager.merge(source_branch, target_branch)

        self.assertTrue(conflict)

    # @patch('push_handler.PushHandler.merge_pair')
    def test_get_branches__local(self):
        #
        self.repo_manager.fetch = MagicMock()

        branches = self.repo_manager.get_branches(remote=False)

        self.repo_manager.fetch.assert_called_once_with()
        self.assertSetEqual(set(branches), {'master', 'develop'})

    # @patch('push_handler.PushHandler.merge_pair')
    def test_get_branches__remote(self):
        #
        self.repo_manager.fetch = MagicMock()

        branches = self.repo_manager.get_branches(remote=True)

        self.repo_manager.fetch.assert_called_once_with()
        self.assertSetEqual(set(branches), {'master', 'develop'})

    def test_push(self):
        self.repo_manager.push('master')
        # TODO: assertions

    def test_fetch(self):
        self.repo_manager.fetch()
        # TODO: assertions
