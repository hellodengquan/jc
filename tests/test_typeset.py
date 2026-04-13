import os
import json
import unittest
import jc.parsers.typeset

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class MyTests(unittest.TestCase):
    maxDiff = None

    with open(os.path.join(THIS_DIR, os.pardir, 'tests/fixtures/generic/typeset.out'), 'r', encoding='utf-8') as f:
        generic_typeset = f.read()

    with open(os.path.join(THIS_DIR, os.pardir, 'tests/fixtures/generic/typeset.json'), 'r', encoding='utf-8') as f:
        generic_typeset_json = json.loads(f.read())

    def test_typeset_nodata(self):
        """
        Test 'typeset' with no data
        """
        self.assertEqual(jc.parsers.typeset.parse('', quiet=True), [])

    def test_typeset_generic(self):
        """
        Test 'typeset' with generic output
        """
        self.assertEqual(jc.parsers.typeset.parse(self.generic_typeset, quiet=True), self.generic_typeset_json)

    def test_typeset_scalar_export(self):
        """
        Test 'typeset' with exported scalar variable
        """
        input_data = 'declare -x MY_VAR="my value"'
        expected = [{
            'name': 'MY_VAR',
            'attributes': ['export'],
            'value': 'my value',
            'type': 'scalar'
        }]
        self.assertEqual(jc.parsers.typeset.parse(input_data, quiet=True), expected)

    def test_typeset_scalar_readonly(self):
        """
        Test 'typeset' with readonly scalar variable
        """
        input_data = 'declare -r READONLY="readonly"'
        expected = [{
            'name': 'READONLY',
            'attributes': ['readonly'],
            'value': 'readonly',
            'type': 'scalar'
        }]
        self.assertEqual(jc.parsers.typeset.parse(input_data, quiet=True), expected)

    def test_typeset_scalar_integer(self):
        """
        Test 'typeset' with integer variable
        """
        input_data = 'declare -i NUM="123"'
        expected = [{
            'name': 'NUM',
            'attributes': ['integer'],
            'value': '123',
            'type': 'scalar'
        }]
        self.assertEqual(jc.parsers.typeset.parse(input_data, quiet=True), expected)

    def test_typeset_array(self):
        """
        Test 'typeset' with array variable
        """
        input_data = 'declare -a MY_ARRAY=\'([0]="a" [1]="b" [2]="c")\''
        result = jc.parsers.typeset.parse(input_data, quiet=True)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'MY_ARRAY')
        self.assertEqual(result[0]['attributes'], ['array'])
        self.assertEqual(result[0]['type'], 'array')
        self.assertEqual(result[0]['value'], ['a', 'b', 'c'])

    def test_typeset_multiple_attributes(self):
        """
        Test 'typeset' with multiple attributes
        """
        input_data = 'declare -rx MULTI="value"'
        expected = [{
            'name': 'MULTI',
            'attributes': ['readonly', 'export'],
            'value': 'value',
            'type': 'scalar'
        }]
        self.assertEqual(jc.parsers.typeset.parse(input_data, quiet=True), expected)

    def test_typeset_no_attributes(self):
        """
        Test 'typeset' with no attributes (--)
        """
        input_data = 'declare -- PLAIN="plain value"'
        expected = [{
            'name': 'PLAIN',
            'attributes': [],
            'value': 'plain value',
            'type': 'scalar'
        }]
        self.assertEqual(jc.parsers.typeset.parse(input_data, quiet=True), expected)

    def test_typeset_empty_value(self):
        """
        Test 'typeset' with empty value
        """
        input_data = 'declare -x EMPTY='
        expected = [{
            'name': 'EMPTY',
            'attributes': ['export'],
            'value': None,
            'type': 'scalar'
        }]
        self.assertEqual(jc.parsers.typeset.parse(input_data, quiet=True), expected)

    def test_typeset_raw_output(self):
        """
        Test 'typeset' with raw output
        """
        input_data = 'declare -x TEST="value"'
        result = jc.parsers.typeset.parse(input_data, quiet=True, raw=True)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'TEST')


if __name__ == '__main__':
    unittest.main()
