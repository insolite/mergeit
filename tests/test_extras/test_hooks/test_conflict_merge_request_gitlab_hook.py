from unittest.mock import MagicMock

from tests.common import RunnerTest
from mergeit.extras.hooks import ConflictMergeRequestGitlabHook


class MergeRequestGitlabHookTest(RunnerTest):

    def setUp(self):
        super().setUp()
        self.config = {'token': MagicMock(),
                       'url': 'foo',
                       'project_id': 42,
                       'title': 'Merge conflict {source} into {target}'}
        self.gitlab_hook = ConflictMergeRequestGitlabHook(self.push_handler_mock, **self.config)
        self.gitlab_api = MagicMock()
        self.gitlab_hook.gitlab_api = self.gitlab_api

    def test_run__conflicted(self):
        source_branch = 'master'
        target_branch = 'develop'
        conflicted = True
        title = self.gitlab_hook.config['title'].format(source=source_branch, target=target_branch)
        commits = MagicMock()
        last_commit_user_id = MagicMock()
        self.push_handler_mock.commits = commits
        self.gitlab_api.get_last_commit_user_id = MagicMock(return_value=last_commit_user_id)

        self.gitlab_hook.run(source_branch, target_branch, conflicted)

        self.gitlab_api.get_last_commit_user_id.assert_called_once_with(commits)
        self.gitlab_api.create_merge_request.assert_called_once_with(source_branch, target_branch, title, last_commit_user_id)

    def test_run__not_conflicted(self):
        source_branch = 'master'
        target_branch = 'develop'
        conflicted = False
        self.gitlab_api.get_last_commit_user_id = MagicMock()

        self.gitlab_hook.run(source_branch, target_branch, conflicted)

        self.gitlab_api.get_last_commit_user_id.assert_not_called()
        self.gitlab_api.create_merge_request.assert_not_called()