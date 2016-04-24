import re
from unittest.mock import patch, Mock

from extras.filters import NextVersionFilter
from tests.common import FilterTest


class NextVersionFilterTest(FilterTest):

    def setUp(self):
        super().setUp()
        self.next_version_filter = NextVersionFilter(self.push_handler_mock)

    @patch('git.Repo')
    def test_run(self, repo_mock):
        source_branch = 'v1.0'
        next_version = '2.0'
        target_branch = 'v{next_version}'
        source_match = re.match('^v\\d+\\.\\d+$', source_branch)
        # TODO: proper mock like:
        # repo_mock.git.branch.return_value = '   master\n * develop\n   v1.0\n   v2.0'
        self.push_handler_mock.repo = Mock()
        self.push_handler_mock.repo.git.branch.return_value = '   origin/master\n * origin/develop\n   origin/v2.0\n   origin/v1.0'

        new_target_branch = self.next_version_filter.run(source_match, source_branch, target_branch)

        self.assertEqual(new_target_branch, target_branch.format(next_version=next_version))
        # repo_mock.fetch.assert_called_once_with()
