r"""jc - JSON Convert `typeset` and `declare` command output parser

Supports `typeset -p` and `declare -p` output from bash.

Usage (cli):

    $ typeset -p | jc --typeset

or

    $ jc typeset

Usage (module):

    import jc
    result = jc.parse('typeset', typeset_command_output)

Schema:

    [
      {
        "name":       string,
        "attributes": [
                        string
        ],
        "value":      string or integer or array or object
      }
    ]

    Attributes:
      - a: array
      - A: associative array (object)
      - i: integer
      - r: readonly
      - x: exported
      - t: trace
      - u: uppercase
      - l: lowercase
      - n: reference

Examples:

    $ typeset -p | jc --typeset -p
    [
      {
        "name": "EXPORTED_VAR",
        "attributes": ["x"],
        "value": "exported value"
      },
      {
        "name": "READONLY_VAR",
        "attributes": ["r"],
        "value": "readonly value"
      },
      {
        "name": "INTEGER_VAR",
        "attributes": ["i"],
        "value": 42
      },
      {
        "name": "ARRAY_VAR",
        "attributes": ["a"],
        "value": ["item1", "item2", "item 3 with space"]
      },
      {
        "name": "ASSOC_ARRAY",
        "attributes": ["A"],
        "value": {"key1": "value1", "key2": "value2"}
      },
      {
        "name": "EXPORTED_INT",
        "attributes": ["i", "x"],
        "value": 100
      }
    ]

    $ typeset -p | jc --typeset -p -r
    [
      {
        "name": "EXPORTED_VAR",
        "attributes": "-x",
        "value": "exported value"
      },
      {
        "name": "READONLY_VAR",
        "attributes": "-r",
        "value": "readonly value"
      }
    ]
"""
import re
from typing import List, Dict, Union, Any
import jc.utils


class info():
    """Provides parser metadata (version, author, etc.)"""
    version = '1.0'
    description = '`typeset` and `declare` command parser'
    author = 'Kelly Brazil'
    author_email = 'kellyjonbrazil@gmail.com'
    compatible = ['linux', 'darwin', 'cygwin', 'aix', 'freebsd']
    magic_commands = ['typeset', 'declare']
    tags = ['command']


__version__ = info.version

# Pattern to match declare/typeset output
# declare -x VAR="value"
# declare -r VAR="value"
# declare -i VAR="42"
# declare -a VAR='([0]="item1" [1]="item2")'
# declare -A VAR='(["key"]="value")'
# declare -- VAR="value"
DECLARE_PATTERN = re.compile(
    r'^declare\s+(?P<attrs>-[a-zA-Z-]+)\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)=(?P<value>.*)$'
)

# Array element pattern: ([0]="item1" [1]="item2" ...)
ARRAY_ELEMENT_PATTERN = re.compile(r'\[(?P<index>\d+)\]="(?P<value>[^"]*)"')

# Associative array element pattern: (["key"]="value" ...) or ([key]="value" ...)
ASSOC_ARRAY_PATTERN = re.compile(r'\[(?:"(?P<key_quoted>[^"]+)"|(?P<key_unquoted>[a-zA-Z_][a-zA-Z0-9_]*))\]="(?P<value>[^"]*)"')

# Simple quoted value
QUOTED_VALUE_PATTERN = re.compile(r'^"(?P<value>.*)"$')

# Single quoted array value
SINGLE_QUOTED_ARRAY_PATTERN = re.compile(r"^'(?P<content>.*)'$")


def _parse_array_value(value_str: str) -> List[str]:
    """
    Parse array value from typeset output.

    Input: '([0]="item1" [1]="item2" [2]="item 3")'
    Output: ["item1", "item2", "item 3"]
    """
    # Remove outer single quotes if present
    match = SINGLE_QUOTED_ARRAY_PATTERN.match(value_str)
    if match:
        content = match.group('content')
    else:
        content = value_str

    # Handle empty array
    if content == '()':
        return []

    elements = []
    for match in ARRAY_ELEMENT_PATTERN.finditer(content):
        elements.append((int(match.group('index')), match.group('value')))

    # Sort by index and extract values
    elements.sort(key=lambda x: x[0])
    return [v for _, v in elements]


def _parse_assoc_array_value(value_str: str) -> Dict[str, str]:
    """
    Parse associative array value from typeset output.

    Input: '(["key1"]="value1" ["key2"]="value2")'
    Output: {"key1": "value1", "key2": "value2"}
    """
    # Remove outer single quotes if present
    match = SINGLE_QUOTED_ARRAY_PATTERN.match(value_str)
    if match:
        content = match.group('content')
    else:
        content = value_str

    result = {}
    for match in ASSOC_ARRAY_PATTERN.finditer(content):
        # key can be either in key_quoted or key_unquoted group
        key = match.group('key_quoted') if match.group('key_quoted') else match.group('key_unquoted')
        result[key] = match.group('value')

    return result


def _parse_value(value_str: str, attrs: str) -> Union[str, int, List[str], Dict[str, str]]:
    """
    Parse the value part based on attributes.
    """
    # Check for array
    if 'a' in attrs:
        return _parse_array_value(value_str)

    # Check for associative array
    if 'A' in attrs:
        return _parse_assoc_array_value(value_str)

    # Remove outer quotes
    match = QUOTED_VALUE_PATTERN.match(value_str)
    if match:
        value = match.group('value')
    else:
        value = value_str

    # Convert to integer if -i flag is set
    if 'i' in attrs:
        try:
            return int(value)
        except (ValueError, TypeError):
            return value

    return value


def _parse_attributes(attrs_str: str) -> Union[str, List[str]]:
    """
    Parse attribute string into list of individual attributes.
    Input: -ix or -x or --
    Output: ['i', 'x'] or ['x'] or []
    """
    if attrs_str == '--':
        return []
    # Remove leading dash and split into individual characters
    return list(attrs_str.lstrip('-'))


def _process(proc_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Final processing to conform to the schema.
    """
    return proc_data


def parse(data: str, raw: bool = False, quiet: bool = False) -> List[Dict[str, Any]]:
    """
    Main text parsing function

    Parameters:

        data:        (string)  text data to parse
        raw:         (boolean) unprocessed output if True
        quiet:       (boolean) suppress warning messages if True

    Returns:

        List of Dictionaries. Raw or processed structured data.
    """
    jc.utils.compatibility(__name__, info.compatible, quiet)
    jc.utils.input_type_check(data)

    raw_output: List[Dict[str, Any]] = []

    if jc.utils.has_data(data):
        for line in data.splitlines():
            line = line.strip()
            if not line:
                continue

            match = DECLARE_PATTERN.match(line)
            if match:
                attrs_str = match.group('attrs')
                name = match.group('name')
                value_str = match.group('value')

                if raw:
                    entry = {
                        'name': name,
                        'attributes': attrs_str,
                        'value': _parse_value(value_str, attrs_str) if 'a' in attrs_str or 'A' in attrs_str or 'i' in attrs_str else value_str.strip('"')
                    }
                else:
                    attrs_list = _parse_attributes(attrs_str)
                    parsed_value = _parse_value(value_str, attrs_str)
                    entry = {
                        'name': name,
                        'attributes': attrs_list,
                        'value': parsed_value
                    }

                raw_output.append(entry)

    return raw_output
