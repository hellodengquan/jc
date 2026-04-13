import os
import json
import unittest
import jc.parsers.typeset

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class MyTests(unittest.TestCase):
    maxDiff = None

    # input
    with open(os.path.join(THIS_DIR, os.pardir, 'tests/fixtures/generic/typeset.out'), 'r', encoding='utf-8') as f:
        typeset_generic = f.read()

    # output
    with open(os.path.join(THIS_DIR, os.pardir, 'tests/fixtures/generic/typeset.json'), 'r', encoding='utf-8') as f:
        typeset_generic_json = json.loads(f.read())

    with open(os.path.join(THIS_DIR, os.pardir, 'tests/fixtures/generic/typeset-raw.json'), 'r', encoding='utf-8') as f:
        typeset_generic_raw_json = json.loads(f.read())

    def test_typeset_nodata(self):
        """
        Test 'typeset' with no data
        """
        self.assertEqual(jc.parsers.typeset.parse('', quiet=True), [])

    def test_typeset_generic(self):
        """
        Test 'typeset' with generic sample data
        """
        self.assertEqual(jc.parsers.typeset.parse(self.typeset_generic, quiet=True), self.typeset_generic_json)

    def test_typeset_generic_raw(self):
        """
        Test 'typeset' with generic sample data and raw output
        """
        self.assertEqual(jc.parsers.typeset.parse(self.typeset_generic, quiet=True, raw=True), self.typeset_generic_raw_json)


if __name__ == '__main__':
    unittest.main()
