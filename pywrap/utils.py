import os
from functools import partial


def indent_block(block, level):
    lines = block.split(os.linesep)
    indented_lines = map(partial(_indent_line, level=level), lines)
    indented_block = os.linesep.join(indented_lines)
    return indented_block


def _indent_line(line, level):
    if line == "":
        return line
    else:
        return "    " * level + line


def assert_equal_linewise(expected, actual, *args, **kwargs):
    from nose.tools import assert_equal
    expected_lines = expected.split(os.linesep)
    actual_lines = actual.split(os.linesep)
    assert_equal(len(expected_lines), len(actual_lines), *args, **kwargs)
    for eline, aline in zip(expected_lines, actual_lines):
        assert_equal(eline, aline, *args, **kwargs)
