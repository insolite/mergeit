from mergeit.core.safe_dict import SafeDict
from tests.common import MergeitTest


class SafeDictTest(MergeitTest):

    def test_missing(self):
        safe_dict = SafeDict({'foo': 'bar'})
        missing_key = 'missing'
        expected_result = '{' + missing_key + '}'

        # result = safe_dict.__missing__(missing_key)
        result = safe_dict[missing_key]

        self.assertEqual(result, expected_result)