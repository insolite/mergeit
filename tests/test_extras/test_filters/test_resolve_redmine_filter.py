import re
from unittest.mock import patch

from extras.filters import ResolveRedmineFilter
from tests.common import FilterTest


class ResolveRedmineFilterTest(FilterTest):

    def setUp(self):
        super().setUp()
        self.resolve_redmine_filter = ResolveRedmineFilter(self.push_handler_mock)

    @patch('extras.filters.ResolveRedmineFilter.get_statuses')
    @patch('extras.filters.ResolveRedmineFilter.update_task')
    def test_run(self, update_task_mock, get_statuses_mock):
        source_branch = '1234-feature'
        target_branch = 'develop'
        source_match = re.match('^(?P<task_id>\\d+)\\-.+$', source_branch)
        status_id = 1
        get_statuses_mock.return_value = [{'name': 'Resolved', 'id': status_id}]

        new_target_branch = self.resolve_redmine_filter.run(source_match, source_branch, target_branch)

        self.assertEqual(new_target_branch, target_branch)
        update_task_mock.assert_called_once_with(source_match.groupdict()['task_id'], {'status_id': status_id})
