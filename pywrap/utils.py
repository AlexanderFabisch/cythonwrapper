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
def hidden_stdout():
    sys.stdout.flush()
    oldstdout_fno = os.dup(1)
    devnull = os.open(os.devnull, os.O_WRONLY)
    newstdout = os.dup(1)
    os.dup2(devnull, 1)
    os.close(devnull)
    sys.stdout = os.fdopen(newstdout, 'w')
    try:
        yield
    finally:
        os.dup2(oldstdout_fno, 1)


@contextmanager
def hidden_stderr():
    sys.stderr.flush()
    oldstderr_fno = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    newstderr = os.dup(2)
    os.dup2(devnull, 2)
    os.close(devnull)
    sys.stderr = os.fdopen(newstderr, 'w')
    try:
        yield
    finally:
        os.dup2(oldstderr_fno, 2)


def remove_files(filenames):
    for f in filenames:
        if os.path.exists(f):
            os.remove(f)
