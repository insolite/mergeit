import re
from unittest.mock import patch

from extras.filters import VersionRedmineFilter
from tests.common import FilterTest


class VersionRedmineFilterTest(FilterTest):

    def setUp(self):
        super().setUp()
        self.version_redmine_filter = VersionRedmineFilter(self.push_handler_mock)

    @patch('extras.filters.VersionRedmineFilter.get_task')
    def test_run(self, get_task_mock):
        source_branch = '1234-feature'
        target_branch = 'v{redmine_version}'
        version = '1.0'
        source_match = re.match('^(?P<task_id>\\d+)\\-.+$', source_branch)
        get_task_mock.return_value = {'fixed_version': {'name': version}}

        new_target_branch = self.version_redmine_filter.run(source_match, source_branch, target_branch)

        self.assertEqual(new_target_branch, target_branch.format(redmine_version=version))
