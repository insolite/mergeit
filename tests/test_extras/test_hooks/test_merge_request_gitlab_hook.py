from unittest.mock import MagicMock, patch, call
from urllib.parse import urljoin

from tests.common import RunnerTest, ResponseMock
from extras.hooks import MergeRequestGitlabHook
import extras.hooks


class MergeRequestGitlabHookTest(RunnerTest):

    def setUp(self):
        super().setUp()
        self.gitlab_hook = MergeRequestGitlabHook(self.push_handler_mock)
        self.gitlab_hook.config = {'token': MagicMock(),
                                   'url': 'foo',
                                   'project_id': 42,
                                   'title': 'Merge conflict {source} into {target}'}

    def test_get_url(self):
        sub_url = 'url.json'
        expected_url = urljoin(self.gitlab_hook.config['url'], sub_url)

        url = self.gitlab_hook.get_url(sub_url)

        self.assertEqual(url, expected_url)

    def test_get_last_commit_user_id__found(self):
        expected_last_commit_user_id = 24
        url = MagicMock()
        self.gitlab_hook.get_url = MagicMock(return_value=url)
        author_name = 'foo'
        self.push_handler_mock.commits = [{'author': {'name': author_name}}]

        with patch.object(extras.hooks, 'requests') as requests_mock:
            requests_mock.get = MagicMock(return_value=ResponseMock([{'id': 12, 'username': 'bar'},
                                                                     {'id': expected_last_commit_user_id, 'username': author_name}]))
            last_commit_user_id = self.gitlab_hook.get_last_commit_user_id()

        self.gitlab_hook.get_url.assert_called_once_with('/api/v3/projects/{}/users'.format(self.gitlab_hook.config['project_id']))
        requests_mock.get.assert_called_once_with(url, headers={'PRIVATE-TOKEN': self.gitlab_hook.config['token']})
        self.assertEqual(last_commit_user_id, expected_last_commit_user_id)

    def test_get_last_commit_user_id__not_found(self):
        url = MagicMock()
        self.gitlab_hook.get_url = MagicMock(return_value=url)
        author_name = 'foo'
        self.push_handler_mock.commits = [{'author': {'name': author_name}}]

        with patch.object(extras.hooks, 'requests') as requests_mock:
            requests_mock.get = MagicMock(return_value=ResponseMock([{'id': 12, 'username': 'bar'}]))
            last_commit_user_id = self.gitlab_hook.get_last_commit_user_id()

        self.gitlab_hook.get_url.assert_called_once_with('/api/v3/projects/{}/users'.format(self.gitlab_hook.config['project_id']))
        requests_mock.get.assert_called_once_with(url, headers={'PRIVATE-TOKEN': self.gitlab_hook.config['token']})
        self.assertIsNone(last_commit_user_id)

    def test_create_merge_request(self):
        source_branch = 'master'
        target_branch = 'develop'
        title = 'foo'
        url = MagicMock()
        self.gitlab_hook.get_url = MagicMock(return_value=url)
        last_commit_user_id = MagicMock()
        self.gitlab_hook.get_last_commit_user_id = MagicMock(return_value=last_commit_user_id)

        with patch.object(extras.hooks, 'requests') as requests_mock:
            requests_mock.get = MagicMock()
            requests_mock.post = MagicMock()
            self.gitlab_hook.create_merge_request(source_branch, target_branch, title)

        self.gitlab_hook.get_url.assert_called_once_with('/api/v3/projects/{}/merge_requests'.format(self.gitlab_hook.config['project_id']))
        requests_mock.post.assert_called_once_with(url, headers={'PRIVATE-TOKEN': self.gitlab_hook.config['token']},
                                                   json=dict(id=self.gitlab_hook.config['project_id'],
                                                             source_branch=source_branch,
                                                             target_branch=target_branch,
                                                             assignee_id=last_commit_user_id,
                                                             title=title))

    def test_run__conflicted(self):
        source_branch = 'master'
        target_branch = 'develop'
        conflicted = True
        self.gitlab_hook.create_merge_request = MagicMock()
        title = self.gitlab_hook.config['title'].format(source=source_branch, target=target_branch)

        self.gitlab_hook.run(source_branch, target_branch, conflicted)

        self.gitlab_hook.create_merge_request.assert_called_once_with(source_branch, target_branch, title)

    def test_run__not_conflicted(self):
        source_branch = 'master'
        target_branch = 'develop'
        conflicted = False
        self.gitlab_hook.create_merge_request = MagicMock()

        self.gitlab_hook.run(source_branch, target_branch, conflicted)

        self.gitlab_hook.create_merge_request.assert_not_called()