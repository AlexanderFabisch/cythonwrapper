import os
import sys
from contextlib import contextmanager
from functools import partial
import keyword


def lines(*args):
    """Make multi-line string."""
    return os.linesep.join(args)


def indent_block(block, level):
    """Indent code block.

    Parameters
    ----------
    block : str
        Code block that might consist of multiple lines separated by os.linesep

    level : int
        Level of indentation. Each level corresponds to four spaces.
    """
    lines = block.split(os.linesep)
    indented_lines = [_indent_line(line, level=level) for line in lines]
    indented_block = os.linesep.join(indented_lines)
    return indented_block


def _indent_line(line, level):
    if line:
        line = "    " * level + line
    return line


def convert_to_docstring(comment):
    """Convert API documentation to docstring."""
    if comment is None:
        return ""
    comment = _strip_comment_markers(comment)
    return _separate_brief_comment(comment)


def _strip_comment_markers(comment):
    if comment.startswith("/**"):
        comment = comment[3:]
    if comment.endswith("*/"):
        comment = comment[:-2]
    if comment.startswith("///"):
        comment = comment[3:]
    comment = comment.strip()

    lines = comment.split(os.linesep)
    lines = [_strip_comment_line(s) for s in lines]
    return os.linesep.join(lines)


def _strip_comment_line(line):
    line = line.strip()
    if line.startswith("*"):
        line = line[1:].strip()
    return line


def _separate_brief_comment(comment):
    splitted = comment.split(".")
    if len(splitted) > 1:
        brief = splitted[0]
        detailed = ".".join(splitted[1:]).strip()
    else:
        brief = comment
        detailed = ""

    docstring = brief + "."
    if detailed != "":
        docstring += 2 * os.linesep + detailed

    return docstring


def from_camel_case(name):
    """Convert camel case to snake case.

    Function and variable names are usually written in camel case in C++ and
    in snake case in Python.
    """
    new_name = str(name)
    i = 0
    while i < len(new_name):
        if new_name[i].isupper() and i > 0:
            new_name = new_name[:i] + "_" + new_name[i:]
            i += 1
        i += 1
    return new_name.lower()


def make_header(header):
    """Make header for shell output."""
    return lines("+" + "=" * 78 + "+",
                 ("| " + header).ljust(79) + "|",
                 "+" + "=" * 78 + "+")


def file_ending(filename):
    """Extract file ending."""
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
    """Remove files if they exist."""
    for f in filenames:
        if os.path.exists(f):
            os.remove(f)


def replace_keyword_argnames(argname):
    """Replace Python keywords.

    We will add the prefix "_".
    """
    if keyword.iskeyword(argname):
        argname = "_" + argname
    return argname
