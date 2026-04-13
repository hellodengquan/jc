r"""jc - JSON Convert `typeset` and `declare` command output parser

This parser converts the output of the `typeset` or `declare` shell command
into structured JSON. It supports parsing variable attributes, names, and
values, including indexed arrays and associative arrays.

Usage (cli):

    $ typeset | jc --typeset

or

    $ jc typeset

Usage (module):

    import jc
    result = jc.parse('typeset', typeset_command_output)

Schema:

    [
      {
        "name":       string,
        "attributes": string,
        "value":      string/number/array/object
      }
    ]

Examples:

    $ typeset | jc --typeset -p
    [
      {
        "name": "MYVAR",
        "attributes": "xr",
        "value": "hello"
      },
      {
        "name": "MYINT",
        "attributes": "i",
        "value": 42
      },
      {
        "name": "MYARR",
        "attributes": "a",
        "value": ["a", "b", "c"]
      },
      {
        "name": "MYASSOC",
        "attributes": "A",
        "value": {"key1": "val1", "key2": "val2"}
      }
    ]
"""
import re
from typing import List, Dict, Any, Union
from jc.jc_types import JSONDictType
import jc.utils


class info():
    """Provides parser metadata (version, author, etc.)"""
    version = '1.0'
    description = '`typeset`/`declare` command parser'
    author = 'JC Parser'
    author_email = 'parser@example.com'
    compatible = ['linux', 'darwin', 'cygwin', 'win32', 'aix', 'freebsd']
    tags = ['command']
    magic_commands = ['typeset', 'declare']


__version__ = info.version


def _parse_value(value_str: str, attributes: str) -> Union[str, int, List[str], Dict[str, str]]:
    """
    Parse a value string, handling arrays and associative arrays.
    """
    value_str = value_str.strip('"\'')
    
    if 'a' in attributes or 'A' in attributes:
        if value_str.startswith('(') and value_str.endswith(')'):
            array_content = value_str[1:-1].strip()
            if not array_content:
                return [] if 'a' in attributes else {}
            
            index_pattern = r'\[([0-9]+)\]=([^ \)]+)'
            index_matches = list(re.finditer(index_pattern, array_content))
            assoc_pattern = r'\[([^\]]+)\]=([^ \)]+)'
            assoc_matches = list(re.finditer(assoc_pattern, array_content))
            
            if index_matches:
                max_index = max(int(m.group(1)) for m in index_matches)
                result = [''] * (max_index + 1)
                for match in index_matches:
                    idx = int(match.group(1))
                    val = match.group(2)
                    val = val.strip('"\'')
                    result[idx] = val
                return result
            elif assoc_matches:
                result = {}
                for match in assoc_matches:
                    key = match.group(1)
                    val = match.group(2)
                    val = val.strip('"\'')
                    result[key] = val
                return result
            else:
                elements = []
                in_quote = False
                quote_char = None
                current = ''
                i = 0
                while i < len(array_content):
                    char = array_content[i]
                    if char in '"\'':
                        if not in_quote:
                            in_quote = True
                            quote_char = char
                        elif char == quote_char:
                            in_quote = False
                            quote_char = None
                        else:
                            current += char
                    elif char.isspace() and not in_quote:
                        if current:
                            elements.append(current)
                            current = ''
                    else:
                        current += char
                    i += 1
                if current:
                    elements.append(current)
                return [e.strip('"\'') for e in elements]
    
    if 'i' in attributes:
        try:
            return int(value_str)
        except ValueError:
            pass
    
    return value_str


def _process(proc_data: List[JSONDictType]) -> List[JSONDictType]:
    """
    Final processing to conform to the schema.

    Parameters:

        proc_data:   (List of Dictionaries) raw structured data to process

    Returns:

        List of Dictionaries. Structured to conform to the schema.
    """
    return proc_data


def parse(
    data: str,
    raw: bool = False,
    quiet: bool = False
) -> List[JSONDictType]:
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

        line_pattern = re.compile(
            r'^(typeset|export|declare)\s+'
            r'(--\s+|-([a-zA-Z]+)\s+)?'
            r'([a-zA-Z_][a-zA-Z0-9_]*)'
            r'(=(.*))?$'
        )

        for line in filter(None, data.splitlines()):
            line = line.strip()
            match = line_pattern.match(line)
            if match:
                cmd = match.group(1)
                attrs = match.group(3) or ''
                name = match.group(4)
                value = match.group(6) or ''

                if cmd == 'export':
                    attrs = 'x' + attrs

                parsed_value = _parse_value(value, attrs)

                raw_output.append({
                    'name': name,
                    'attributes': attrs,
                    'value': parsed_value
                })

    return raw_output if raw else _process(raw_output)
