import os
import sys
import warnings
import numpy as np
from contextlib import contextmanager
from .cython import make_cython_wrapper, write_files, run_setup
from .defaultconfig import Config
from .utils import file_ending, remove_files

PREFIX = os.sep.join(__file__.split(os.sep)[:-2] + ["test"])
SETUPPY_NAME = "setup_test.py"


def full_paths(filenames):
    """Get absolute paths of files in the test directory.

    Parameters
    ----------
    filenames : iterable or str
        List of filenames or one filename of files that are in the test
        directory. These files MUST be located in the test directory.

    Returns
    -------
    full_paths : list
        Full paths of the files.
    """
    if isinstance(filenames, str):
        filenames = [filenames]

    if PREFIX == "":
        return filenames
    else:
        attach_prefix = lambda filename: (filename if filename.startswith("/")
                                          else os.path.join(PREFIX, filename))
        full_paths = list(map(attach_prefix, filenames))
        for path in full_paths:
            assert os.path.exists(path)
        return full_paths


@contextmanager
def cython_extension_from(headers, modulename=None, config=Config(),
                          assert_warn=None, warn_msg=None, incdirs=[],
                          hide_errors=False, cleanup=True):
    incdirs = full_paths(incdirs)
    filenames = _write_cython_wrapper(full_paths(headers), modulename,
                                      config, incdirs, assert_warn, warn_msg)
    run_setup(SETUPPY_NAME, hide_errors)
    try:
        yield
    finally:
        if cleanup:
            remove_files(filenames)


def _write_cython_wrapper(filenames, modulename, config, incdirs, assert_warn,
                          warn_msg, verbose=0):
    kwargs = {
        "filenames": filenames,
        "sources": [],
        "modulename": modulename,
        "config": config,
        "target": ".",
        "incdirs": incdirs,
        "verbose": verbose,
        "compiler_flags": ["-O0"]
    }
    if assert_warn is None:
        results = make_cython_wrapper(**kwargs)
    else:
        results = assert_warns_message(
            assert_warn, warn_msg, make_cython_wrapper, **kwargs)
    results[SETUPPY_NAME] = results["setup.py"]
    del results["setup.py"]
    write_files(results)

    filenames = []
    filenames.extend(results.keys())

    temporary_files = []
    for filename in filenames:
        if filename.endswith(".pyx"):
            temporary_files.append(filename.replace(
                file_ending(filename), "cpp"))
            temporary_files.append(filename.replace(
                file_ending(filename), "so"))
    filenames.extend(temporary_files)

    return filenames


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
    for mod in list(sys.modules.values()):
        if hasattr(mod, reg):
            getattr(mod, reg).clear()
