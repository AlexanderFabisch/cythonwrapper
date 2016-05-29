import os
import sys
from contextlib import contextmanager
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


def file_ending(filename):
    return filename.split(".")[-1]


@contextmanager
def hidden_stream(fileno):
    """Hide output stream."""
    if fileno not in [1, 2]:
        raise ValueError("Expected fileno 1 or 2.")
    stream_name = ["stdout", "stderr"][fileno - 1]
    getattr(sys, stream_name).flush()
    oldstream_fno = os.dup(fileno)
    devnull = os.open(os.devnull, os.O_WRONLY)
    newstream = os.dup(fileno)
    os.dup2(devnull, fileno)
    os.close(devnull)
    setattr(sys, stream_name, os.fdopen(newstream, 'w'))
    try:
        yield
    finally:
        os.dup2(oldstream_fno, fileno)


hidden_stdout = partial(hidden_stream, fileno=1)
hidden_stderr = partial(hidden_stream, fileno=2)


def remove_files(filenames):
    for f in filenames:
        if os.path.exists(f):
            os.remove(f)
