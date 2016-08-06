from unittest.mock import MagicMock, patch
from urllib.parse import urljoin

from tests.common import RunnerTest, ResponseMock
from extras.api.gitlab_api import GitlabApi
import extras.api.gitlab_api


class MergeRequestGitlabHookTest(RunnerTest):

    def setUp(self):
        super().setUp()
        self.url = 'foo'
        self.project_id = 42
        self.token = MagicMock()
        self.gitlab_api = GitlabApi(self.url, self.project_id, self.token)

    def test_get_url(self):
        sub_url = 'url.json'
        expected_url = urljoin(self.url, sub_url)

        url = self.gitlab_api.get_url(sub_url)

        self.assertEqual(url, expected_url)

    def test_get_last_commit_user_id__found(self):
        expected_last_commit_user_id = 24
        url = MagicMock()
        self.gitlab_api.get_url = MagicMock(return_value=url)
        author_name = 'foo'
        commits = [{'author': {'name': author_name}}]

        with patch.object(extras.api.gitlab_api, 'requests') as requests_mock:
            requests_mock.get = MagicMock(return_value=ResponseMock([{'id': 12, 'username': 'bar'},
                                                                     {'id': expected_last_commit_user_id, 'username': author_name}]))
            last_commit_user_id = self.gitlab_api.get_last_commit_user_id(commits)

        self.gitlab_api.get_url.assert_called_once_with('/api/v3/projects/{}/users'.format(self.project_id))
        requests_mock.get.assert_called_once_with(url, headers={'PRIVATE-TOKEN': self.token})
        self.assertEqual(last_commit_user_id, expected_last_commit_user_id)

    def test_get_last_commit_user_id__not_found(self):
        url = MagicMock()
        self.gitlab_api.get_url = MagicMock(return_value=url)
        author_name = 'foo'
        commits = [{'author': {'name': author_name}}]

        with patch.object(extras.api.gitlab_api, 'requests') as requests_mock:
            requests_mock.get = MagicMock(return_value=ResponseMock([{'id': 12, 'username': 'bar'}]))
            last_commit_user_id = self.gitlab_api.get_last_commit_user_id(commits)

        self.gitlab_api.get_url.assert_called_once_with('/api/v3/projects/{}/users'.format(self.project_id))
        requests_mock.get.assert_called_once_with(url, headers={'PRIVATE-TOKEN': self.token})
        self.assertIsNone(last_commit_user_id)

    def test_create_merge_request(self):
        source_branch = 'master'
        target_branch = 'develop'
        title = 'foo'
        url = MagicMock()
        self.gitlab_api.get_url = MagicMock(return_value=url)
        last_commit_user_id = MagicMock()

        with patch.object(extras.api.gitlab_api, 'requests') as requests_mock:
            requests_mock.get = MagicMock()
            requests_mock.post = MagicMock()
            self.gitlab_api.create_merge_request(source_branch, target_branch, title, last_commit_user_id)

        self.gitlab_api.get_url.assert_called_once_with('/api/v3/projects/{}/merge_requests'.format(self.project_id))
        requests_mock.post.assert_called_once_with(url, headers={'PRIVATE-TOKEN': self.token},
                                                   json=dict(id=self.project_id,
                                                             source_branch=source_branch,
                                                             target_branch=target_branch,
                                                             assignee_id=last_commit_user_id,
                                                             title=title))
