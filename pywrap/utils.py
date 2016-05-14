import os
from functools import partial


def lines(*args):
    return os.linesep.join(args)


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


def from_camel_case(name):
    new_name = str(name)
    i = 0
    while i < len(new_name):
        if new_name[i].isupper() and i > 0:
            new_name = new_name[:i] + "_" + new_name[i:]
            i += 1
        i += 1
    return new_name.lower()


def make_header(header):
    return lines("+" + "=" * 78 + "+",
                 ("| " + header).ljust(79) + "|",
                 "+" + "=" * 78 + "+")
