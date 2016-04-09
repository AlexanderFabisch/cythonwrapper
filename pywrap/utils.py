import os
import sys
import warnings
from functools import partial
import numpy as np


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


def from_camel_case(name):
    new_name = str(name)
    i = 0
    while i < len(new_name):
        if new_name[i].isupper():
            new_name = new_name[:i] + "_" + new_name[i:]
            i += 1
        i += 1
    return new_name.lower()


# from scikit-klearn
def assert_warns_message(warning_class, message, func, *args, **kw):
    # very important to avoid uncontrolled state propagation
    """Test that a certain warning occurs and with a certain message.

    Parameters
    ----------
    warning_class : the warning class
        The class to test for, e.g. UserWarning.

    message : str | callable
        The entire message or a substring to  test for. If callable,
        it takes a string as argument and will trigger an assertion error
        if it returns `False`.

    func : callable
        Calable object to trigger warnings.

    *args : the positional arguments to `func`.

    **kw : the keyword arguments to `func`.

    Returns
    -------

    result : the return value of `func`

    """
    clean_warning_registry()
    with warnings.catch_warnings(record=True) as w:
        # Cause all warnings to always be triggered.
        warnings.simplefilter("always")
        if hasattr(np, 'VisibleDeprecationWarning'):
            # Let's not catch the numpy internal DeprecationWarnings
            warnings.simplefilter('ignore', np.VisibleDeprecationWarning)
        # Trigger a warning.
        result = func(*args, **kw)
        # Verify some things
        if not len(w) > 0:
            raise AssertionError("No warning raised when calling %s"
                                 % func.__name__)

        found = [issubclass(warning.category, warning_class) for warning in w]
        if not any(found):
            raise AssertionError("No warning raised for %s with class "
                                 "%s"
                                 % (func.__name__, warning_class))

        message_found = False
        # Checks the message of all warnings belong to warning_class
        for index in [i for i, x in enumerate(found) if x]:
            # substring will match, the entire message with typo won't
            msg = w[index].message  # For Python 3 compatibility
            msg = str(msg.args[0] if hasattr(msg, 'args') else msg)
            if callable(message):  # add support for certain tests
                check_in_message = message
            else:
                check_in_message = lambda msg: message in msg

            if check_in_message(msg):
                message_found = True
                break

        if not message_found:
            raise AssertionError("Did not receive the message you expected "
                                 "('%s') for <%s>, got: '%s'"
                                 % (message, func.__name__, msg))

    return result


def clean_warning_registry():
    """Safe way to reset warnings """
    warnings.resetwarnings()
    reg = "__warningregistry__"
    for mod_name, mod in list(sys.modules.items()):
        if 'six.moves' in mod_name:
            continue
        if hasattr(mod, reg):
            getattr(mod, reg).clear()