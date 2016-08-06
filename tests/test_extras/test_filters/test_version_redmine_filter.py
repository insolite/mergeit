import re
from unittest.mock import MagicMock

from extras.filters import VersionRedmineFilter
from tests.common import RunnerTest


class VersionRedmineFilterTest(RunnerTest):

    def setUp(self):
        super().setUp()
        self.version_redmine_filter = VersionRedmineFilter(self.push_handler_mock)

    def test_run(self):
        source_branch = '1234-feature'
        target_branch = 'v{redmine_version}'
        version = '1.0'
        source_match = re.match('^(?P<task_id>\\d+)\\-.+$', source_branch)
        self.version_redmine_filter.get_task = MagicMock(return_value={'fixed_version': {'name': version}})

        new_target_branch = self.version_redmine_filter.run(source_match, source_branch, target_branch)

        self.assertEqual(new_target_branch, target_branch.format(redmine_version=version))
        self.version_redmine_filter.get_task.assert_called_once_with(source_match.groupdict()['task_id'])
