import re
from unittest.mock import MagicMock, call

from mergeit.extras.filters import NextVersionFilter
from tests.common import RunnerTest


class NextVersionFilterTest(RunnerTest):

    def setUp(self):
        super().setUp()
        self.next_version_filter = NextVersionFilter(self.push_handler_mock)

    def test_get_version__semantic_v(self):
        expected_version_number = 4.2
        branch = 'v{}'.format(expected_version_number)

        version_number = self.next_version_filter.get_version(branch)

        self.assertEqual(version_number, expected_version_number)

    def test_get_version__semantic_no_v(self):
        expected_version_number = 4.2
        branch = '{}'.format(expected_version_number)

        version_number = self.next_version_filter.get_version(branch)

        self.assertEqual(version_number, expected_version_number)

    def test_get_version__verbose(self):
        expected_version_number = -1
        branch = 'master'

        version_number = self.next_version_filter.get_version(branch)

        self.assertEqual(version_number, expected_version_number)

    def test_run(self):
        source_branch = 'v1.0'
        next_version = '2.0'
        target_branch = 'v{next_version}'
        source_match = re.match('^v\\d+\\.\\d+$', source_branch)
        branches = ['master', 'develop', 'v2.0', 'v1.0']
        self.push_handler_mock.get_branches.return_value = branches
        self.next_version_filter.get_version = MagicMock(side_effect=[-1, -1, 2.0, 1.0])

        new_target_branch = self.next_version_filter.run(source_match, source_branch, target_branch)

        self.assertEqual(new_target_branch, target_branch.format(next_version=next_version))
        self.push_handler_mock.get_branches.assert_called_once_with(remote=True)
        self.next_version_filter.get_version.assert_has_calls([call(branch) for branch in branches], any_order=False) # TODO: actually any_order=True, but how to map args and return_values?
        # repo_mock.fetch.assert_called_once_with()

    def test_run__no_next(self):
        source_branch = 'v1.0'
        target_branch = 'v{next_version}'
        source_match = re.match('^v\\d+\\.\\d+$', source_branch)
        branches = ['master', 'develop', 'v1.0']
        self.push_handler_mock.get_branches.return_value = branches
        self.next_version_filter.get_version = MagicMock(side_effect=[-1, -1, 1.0])

        new_target_branch = self.next_version_filter.run(source_match, source_branch, target_branch)

        self.assertIsNone(new_target_branch)
        self.push_handler_mock.get_branches.assert_called_once_with(remote=True)
        self.next_version_filter.get_version.assert_has_calls([call(branch) for branch in branches], any_order=False) # TODO: actually any_order=True, but how to map args and return_values?
        # repo_mock.fetch.assert_called_once_with()
