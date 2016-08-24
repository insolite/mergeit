from unittest.mock import patch, MagicMock
from urllib.parse import urljoin

from mergeit.extras.filters import RedmineFilter
from tests.common import RunnerTest, ResponseMock
import mergeit.extras.filters.redmine_filter


class RedmineFilterTest(RunnerTest):

    def setUp(self):
        super().setUp()
        self.redmine_filter = RedmineFilter(self.push_handler_mock)
        self.redmine_filter.config = {'api_key': MagicMock(),
                                      'url': 'foo'}

    def test_get_url(self):
        sub_url = 'url.json'
        expected_url = urljoin(self.redmine_filter.config['url'], sub_url)

        url = self.redmine_filter.get_url(sub_url)

        self.assertEqual(url, expected_url)

    def test_get_task(self):
        task_id = 42
        expected_issue_data = {'data': {}} # TODO: real response
        url = MagicMock()
        self.redmine_filter.get_url = MagicMock(return_value=url)

        with patch.object(mergeit.extras.filters.redmine_filter, 'requests') as requests_mock:
            requests_mock.get = MagicMock(return_value=ResponseMock({'issue': expected_issue_data}))
            issue_data = self.redmine_filter.get_task(task_id)

        self.assertEqual(issue_data, expected_issue_data)
        self.redmine_filter.get_url.assert_called_once_with('/issues/{}.json'.format(task_id))
        requests_mock.get.assert_called_once_with(url, data={'key': self.redmine_filter.config['api_key']})

    def test_update_task(self):
        task_id = 42
        issue_data = {'data': {}} # TODO: real response
        url = MagicMock()
        self.redmine_filter.get_url = MagicMock(return_value=url)

        with patch.object(mergeit.extras.filters.redmine_filter, 'requests') as requests_mock:
            requests_mock.put = MagicMock()
            self.redmine_filter.update_task(task_id, issue_data)

        self.redmine_filter.get_url.assert_called_once_with('/issues/{}.json'.format(task_id))
        requests_mock.put.assert_called_once_with(url, json={'key': self.redmine_filter.config['api_key'],
                                                             'issue': issue_data})

    def test_get_statuses(self):
        expected_issue_statuses = [{'name': 'Resolved'}] # TODO: real response
        url = MagicMock()
        self.redmine_filter.get_url = MagicMock(return_value=url)

        with patch.object(mergeit.extras.filters.redmine_filter, 'requests') as requests_mock:
            requests_mock.get = MagicMock(return_value=ResponseMock({'issue_statuses': expected_issue_statuses}))
            issue_data = self.redmine_filter.get_statuses()

        self.assertEqual(issue_data, expected_issue_statuses)
        self.redmine_filter.get_url.assert_called_once_with('/issue_statuses.json')
        requests_mock.get.assert_called_once_with(url, data={'key': self.redmine_filter.config['api_key']})
