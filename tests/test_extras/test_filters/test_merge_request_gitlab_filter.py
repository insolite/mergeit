from unittest.mock import MagicMock

from tests.common import RunnerTest
from mergeit.extras.filters.merge_request_gitlab_filter import MergeRequestGitlabFilter


class MergeRequestGitlabFilterTest(RunnerTest):

    def setUp(self):
        super().setUp()
        self.config = {'token': MagicMock(),
                       'url': 'foo',
                       'project_id': 42,
                       'title': 'Merge approval {source} into {target}',
                       'user_id': 24}
        self.gitlab_filter = MergeRequestGitlabFilter(self.push_handler_mock, **self.config)
        self.gitlab_api = MagicMock()
        self.gitlab_filter.gitlab_api = self.gitlab_api

    def test_run__no_user_defined(self):
        conflicted = MagicMock()
        source_branch = 'stage'
        target_branch = 'master'
        title = self.gitlab_filter.config['title'].format(source=source_branch, target=target_branch)
        commits = MagicMock()
        last_commit_user_id = MagicMock()
        self.push_handler_mock.commits = commits
        self.gitlab_api.get_last_commit_user_id = MagicMock(return_value=last_commit_user_id)
        self.gitlab_filter.config.pop('user_id', None)

        self.gitlab_filter.run(conflicted, source_branch, target_branch)

        self.gitlab_api.get_last_commit_user_id.assert_called_once_with(commits)
        self.gitlab_api.create_merge_request.assert_called_once_with(source_branch, target_branch, title, last_commit_user_id)

    def test_run__user_defined(self):
        source_match = MagicMock()
        source_branch = 'stage'
        target_branch = 'master'
        title = self.gitlab_filter.config['title'].format(source=source_branch, target=target_branch)
        self.gitlab_api.get_last_commit_user_id = MagicMock()

        self.gitlab_filter.run(source_match, source_branch, target_branch)

        self.gitlab_api.get_last_commit_user_id.assert_not_called()
        self.gitlab_api.create_merge_request.assert_called_once_with(source_branch, target_branch, title, self.config['user_id'])