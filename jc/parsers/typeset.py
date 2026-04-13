r"""jc - JSON Convert `typeset` and `declare` command output parser

This parser converts the output of the `typeset -p` or `declare -p` command
into structured JSON format. Each variable declaration is parsed into its
component parts: name, attributes, and value.

Usage (cli):

    $ typeset -p | jc --typeset

or

    $ declare -p | jc --typeset

or

    $ jc typeset

Usage (module):

    import jc
    result = jc.parse('typeset', typeset_command_output)

Schema:

    [
      {
        "name":         string,
        "attributes":   array of strings,  # e.g., ["readonly", "export"]
        "value":        string or array or object,  # depends on variable type
        "type":         string  # "scalar", "array", or "associative_array"
      }
    ]

Examples:

    $ typeset -p | jc --typeset -p
    [
      {
        "name": "PATH",
        "attributes": ["export"],
        "value": "/usr/local/bin:/usr/bin:/bin",
        "type": "scalar"
      },
      {
        "name": "my_array",
        "attributes": ["array"],
        "value": ["a", "b", "c"],
        "type": "array"
      },
      {
        "name": "readonly_var",
        "attributes": ["readonly", "export"],
        "value": "some value",
        "type": "scalar"
      }
    ]
"""
import re
import jc.utils


class info():
    """Provides parser metadata (version, author, etc.)"""
    version = '1.0'
    description = '`typeset` and `declare` command parser'
    author = 'jc'
    author_email = 'jc@example.com'
    compatible = ['linux', 'darwin', 'cygwin', 'aix', 'freebsd']
    magic_commands = ['typeset', 'declare']
    tags = ['command']


__version__ = info.version

ATTRIBUTE_MAP = {
    'a': 'array',
    'A': 'associative_array',
    'i': 'integer',
    'r': 'readonly',
    'x': 'export',
    'l': 'lowercase',
    'u': 'uppercase',
    'n': 'nameref',
    't': 'trace',
    'f': 'function',
    'F': 'function',
    'I': 'capitalize',
}

DECLARE_PATTERN = re.compile(
    r'^declare\s+'
    r'(-[aAiIlLnrtux]*|--)?\s*'
    r'([a-zA-Z_][a-zA-Z0-9_]*)\s*'
    r'=?'
    r'(.*)$'
)

ARRAY_PATTERN = re.compile(r'\((.*)\)$')
ARRAY_ELEMENT_PATTERN = re.compile(r'\[(\d+|"[^"]+"|\'[^\']+\'|[^\]]+)\]="([^"]*)"|\[(\d+|"[^"]+"|\'[^\']+\'|[^\]]+)\]=\'([^\']*)\'|\[(\d+|"[^"]+"|\'[^\']+\'|[^\]]+)\]=([^"\s][^)]*)')


def _parse_attributes(attr_str):
    """Parse attribute string like '-rx' or '--' into list of attribute names."""
    if not attr_str or attr_str == '--':
        return []

    attr_str = attr_str.strip()
    if attr_str.startswith('-'):
        attr_str = attr_str[1:]

    attributes = []
    for char in attr_str:
        if char in ATTRIBUTE_MAP:
            attributes.append(ATTRIBUTE_MAP[char])

    return attributes


def _parse_array_value(value_str):
    """Parse array value string like '([0]="a" [1]="b")' into a list."""
    match = ARRAY_PATTERN.match(value_str.strip())
    if not match:
        return value_str

    inner = match.group(1)
    elements = []
    index_map = {}

    pos = 0
    while pos < len(inner):
        if inner[pos] == '[':
            end_bracket = inner.find(']=', pos)
            if end_bracket == -1:
                break

            index_str = inner[pos+1:end_bracket]
            pos = end_bracket + 2

            if pos >= len(inner):
                break

            if inner[pos] == '"':
                end_quote = inner.find('"', pos + 1)
                if end_quote != -1:
                    value = inner[pos+1:end_quote]
                    pos = end_quote + 1
                else:
                    break
            elif inner[pos] == "'":
                end_quote = inner.find("'", pos + 1)
                if end_quote != -1:
                    value = inner[pos+1:end_quote]
                    pos = end_quote + 1
                else:
                    break
            else:
                end_value = pos
                while end_value < len(inner) and inner[end_value] not in ' \t':
                    end_value += 1
                value = inner[pos:end_value]
                pos = end_value

            try:
                idx = int(index_str)
                index_map[idx] = value
            except ValueError:
                pass

            while pos < len(inner) and inner[pos] in ' \t':
                pos += 1
        else:
            pos += 1

    if index_map:
        max_idx = max(index_map.keys()) if index_map else -1
        elements = [''] * (max_idx + 1)
        for idx, val in index_map.items():
            elements[idx] = val

    return elements if elements else value_str


def _parse_associative_array_value(value_str):
    """Parse associative array value like '([key1]="val1" [key2]="val2")' into a dict."""
    match = ARRAY_PATTERN.match(value_str.strip())
    if not match:
        return value_str

    inner = match.group(1)
    result = {}

    pos = 0
    while pos < len(inner):
        if inner[pos] == '[':
            end_bracket = inner.find(']=', pos)
            if end_bracket == -1:
                break

            key_str = inner[pos+1:end_bracket]
            key_str = key_str.strip('"\'')
            pos = end_bracket + 2

            if pos >= len(inner):
                break

            if inner[pos] == '"':
                end_quote = inner.find('"', pos + 1)
                if end_quote != -1:
                    value = inner[pos+1:end_quote]
                    pos = end_quote + 1
                else:
                    break
            elif inner[pos] == "'":
                end_quote = inner.find("'", pos + 1)
                if end_quote != -1:
                    value = inner[pos+1:end_quote]
                    pos = end_quote + 1
                else:
                    break
            else:
                end_value = pos
                while end_value < len(inner) and inner[end_value] not in ' \t':
                    end_value += 1
                value = inner[pos:end_value]
                pos = end_value

            result[key_str] = value

            while pos < len(inner) and inner[pos] in ' \t':
                pos += 1
        else:
            pos += 1

    return result if result else value_str


def _parse_value(value_str, attributes):
    """Parse the value based on attributes."""
    if not value_str:
        return None

    value_str = value_str.strip()

    if value_str.startswith("'") and value_str.endswith("'"):
        value_str = value_str[1:-1]
    elif value_str.startswith('"') and value_str.endswith('"'):
        value_str = value_str[1:-1]

    if 'array' in attributes and value_str.startswith('('):
        return _parse_array_value(value_str)

    if 'associative_array' in attributes and value_str.startswith('('):
        return _parse_associative_array_value(value_str)

    return value_str


def _determine_type(attributes):
    """Determine the variable type from attributes."""
    if 'associative_array' in attributes:
        return 'associative_array'
    if 'array' in attributes:
        return 'array'
    return 'scalar'


def _process(proc_data):
    """
    Final processing to conform to the schema.

    Parameters:

        proc_data:   (List of Dictionaries) raw structured data to process

    Returns:

        List of Dictionaries. Structured data to conform to the schema.
    """
    return proc_data


def parse(data, raw=False, quiet=False):
    """
    Main text parsing function

    Parameters:

        data:        (string)  text data to parse
        raw:         (boolean) unprocessed output if True
        quiet:       (boolean) suppress warning messages if True

    Returns:

        List of Dictionaries of structured data
    """
    jc.utils.compatibility(__name__, info.compatible, quiet)
    jc.utils.input_type_check(data)

    raw_output = []

    if jc.utils.has_data(data):
        for line in data.splitlines():
            line = line.strip()
            if not line:
                continue

            match = DECLARE_PATTERN.match(line)
            if match:
                attr_str = match.group(1) or ''
                name = match.group(2)
                value_str = match.group(3) or ''

                attributes = _parse_attributes(attr_str)

                value = _parse_value(value_str, attributes)

                var_type = _determine_type(attributes)

                entry = {
                    'name': name,
                    'attributes': attributes,
                    'value': value,
                    'type': var_type
                }

                raw_output.append(entry)

    return raw_output if raw else _process(raw_output)
