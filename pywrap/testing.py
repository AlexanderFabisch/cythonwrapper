import os
import sys
import warnings
from contextlib import contextmanager

import numpy as np

from pywrap import cython

PREFIX = os.sep.join(__file__.split(os.sep)[:-2]) + os.sep + "test"
SETUPPY_NAME = "setup_test.py"


def full_paths(filenames):
    if isinstance(filenames, str):
        filenames = [filenames]

    if PREFIX == "":
        return filenames
    else:
        attach_prefix = lambda filename: PREFIX + os.sep + filename
        return map(attach_prefix, filenames)


@contextmanager
def cython_extension_from(headers, modulename=None, custom_config=None,
                          assert_warn=None, warn_msg=None, cleanup=True):
    if custom_config is not None:
        custom_config = full_paths(custom_config)[0]
    filenames = _write_cython_wrapper(full_paths(headers), modulename,
                                      custom_config, assert_warn, warn_msg)
    _run_setup()
    try:
        yield
    finally:
        if cleanup:
            _remove_files(filenames)


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


def _write_cython_wrapper(filenames, modulename, custom_config, assert_warn,
                          warn_msg, verbose=0):
    if assert_warn is None:
        results, cython_files = cython.make_cython_wrapper(
            filenames, sources=[], modulename=modulename,
            custom_config=custom_config, target=".", verbose=verbose)
    else:
        results, cython_files = assert_warns_message(
            assert_warn, warn_msg, cython.make_cython_wrapper,
            filenames, sources=[], modulename=modulename,
            custom_config=custom_config, target=".", verbose=verbose)
    results[SETUPPY_NAME] = results["setup.py"]
    del results["setup.py"]
    cython.write_files(results)
    cython.cython(cython_files)

    filenames = []
    filenames.extend(results.keys())
    for filename in cython_files:
        filenames.append(filename.replace(cython.file_ending(filename), "cpp"))
        filenames.append(filename.replace(cython.file_ending(filename), "so"))
    return filenames


def _run_setup():
    with hidden_stdout():
        os.system("python %s build_ext -i" % SETUPPY_NAME)


def _remove_files(filenames):
    for f in filenames:
        if os.path.exists(f):
            os.remove(f)


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
        if hasattr(mod, reg):
            getattr(mod, reg).clear()
