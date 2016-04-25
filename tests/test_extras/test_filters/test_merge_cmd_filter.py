import re
from unittest.mock import patch, Mock

from extras.filters import MergeCmdFilter
from tests.common import FilterTest


class NextVersionFilterTest(FilterTest):

    def setUp(self):
        super().setUp()
        self.merge_cmd_filter = MergeCmdFilter(self.push_handler_mock)

    def test_run_merge(self):
        source_branch = '1234-feature'
        target_branch = 'develop'
        source_match = re.match('^(?P<task_id>\\d+)\\-.+$', source_branch)
        # TODO: proper mock
        self.push_handler_mock.commits = [{'message': 'Add new feature\nResolve #1234\n@merge'}]

        new_target_branch = self.merge_cmd_filter.run(source_match, source_branch, target_branch)

        self.assertEqual(new_target_branch, target_branch)

    def test_run_do_not_merge(self):
        source_branch = '1234-feature'
        target_branch = 'develop'
        source_match = re.match('^(?P<task_id>\\d+)\\-.+$', source_branch)
        # TODO: proper mock
        self.push_handler_mock.commits = [{'message': 'Add new feature\nResolve #1234'}]

        new_target_branch = self.merge_cmd_filter.run(source_match, source_branch, target_branch)

        self.assertIsNone(new_target_branch)
