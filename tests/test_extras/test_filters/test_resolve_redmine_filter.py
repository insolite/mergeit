import re
from unittest.mock import MagicMock

from extras.filters import ResolveRedmineFilter
from tests.common import RunnerTest


class ResolveRedmineFilterTest(RunnerTest):

    def setUp(self):
        super().setUp()
        self.resolve_redmine_filter = ResolveRedmineFilter(self.push_handler_mock)

    def test_run__resolve(self):
        source_branch = '1234-feature'
        target_branch = 'develop'
        source_match = re.match('^(?P<task_id>\\d+)\\-.+$', source_branch)
        status_id = 1
        self.push_handler_mock.commits = [{'message': 'Add new feature\n@resolve\nFix bugs'}]
        self.resolve_redmine_filter.get_statuses = MagicMock(return_value=[{'name': 'Resolved', 'id': status_id}])
        self.resolve_redmine_filter.update_task = MagicMock()

        new_target_branch = self.resolve_redmine_filter.run(source_match, source_branch, target_branch)

        self.assertEqual(new_target_branch, target_branch)
        self.resolve_redmine_filter.get_statuses.assert_called_once_with()
        self.resolve_redmine_filter.update_task.assert_called_once_with(source_match.groupdict()['task_id'], {'status_id': status_id})

    def test_run__not_resolve(self):
        source_branch = '1234-feature'
        target_branch = 'develop'
        source_match = re.match('^(?P<task_id>\\d+)\\-.+$', source_branch)
        status_id = 1
        self.push_handler_mock.commits = [{'message': 'Add new feature\nFix bugs'}]
        self.resolve_redmine_filter.get_statuses = MagicMock(return_value=[{'name': 'Resolved', 'id': status_id}])
        self.resolve_redmine_filter.update_task = MagicMock()

        new_target_branch = self.resolve_redmine_filter.run(source_match, source_branch, target_branch)

        self.assertEqual(new_target_branch, target_branch)
        self.resolve_redmine_filter.get_statuses.assert_not_called()
        self.resolve_redmine_filter.update_task.assert_not_called()
