import re
from unittest.mock import patch, Mock

from extras.filters import NextVersionFilter
from tests.common import FilterTest


class NextVersionFilterTest(FilterTest):

    def setUp(self):
        super().setUp()
        self.next_version_filter = NextVersionFilter(self.push_handler_mock)

    # @patch('push_handler.PushHandler.get_branches')
    def test_run(self): # , get_branches_mock
        source_branch = 'v1.0'
        next_version = '2.0'
        target_branch = 'v{next_version}'
        source_match = re.match('^v\\d+\\.\\d+$', source_branch)
        # TODO: proper mock like:
        # get_branches_mock.return_value = ['master', 'develop', 'v2.0', 'v1.0']
        self.push_handler_mock.get_branches.return_value = ['master', 'develop', 'v2.0', 'v1.0']

        new_target_branch = self.next_version_filter.run(source_match, source_branch, target_branch)

        self.assertEqual(new_target_branch, target_branch.format(next_version=next_version))
        # repo_mock.fetch.assert_called_once_with()
