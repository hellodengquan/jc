import os
import json
import unittest
import jc.parsers.typeset

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class MyTests(unittest.TestCase):
    maxDiff = None

    with open(os.path.join(THIS_DIR, os.pardir, 'tests/fixtures/generic/typeset-bash.out'), 'r', encoding='utf-8') as f:
        typeset_bash = f.read()

    with open(os.path.join(THIS_DIR, os.pardir, 'tests/fixtures/generic/typeset-zsh.out'), 'r', encoding='utf-8') as f:
        typeset_zsh = f.read()

    with open(os.path.join(THIS_DIR, os.pardir, 'tests/fixtures/generic/typeset-bash.json'), 'r', encoding='utf-8') as f:
        typeset_bash_json = json.loads(f.read())

    with open(os.path.join(THIS_DIR, os.pardir, 'tests/fixtures/generic/typeset-zsh.json'), 'r', encoding='utf-8') as f:
        typeset_zsh_json = json.loads(f.read())


    def test_typeset_nodata(self):
        """
        Test 'typeset' with no data
        """
        self.assertEqual(jc.parsers.typeset.parse('', quiet=True), [])

    def test_typeset_bash(self):
        """
        Test 'declare' (bash) output
        """
        self.assertEqual(jc.parsers.typeset.parse(self.typeset_bash, quiet=True), self.typeset_bash_json)

    def test_typeset_zsh(self):
        """
        Test 'typeset' (zsh) output
        """
        self.assertEqual(jc.parsers.typeset.parse(self.typeset_zsh, quiet=True), self.typeset_zsh_json)


if __name__ == '__main__':
    unittest.main()
