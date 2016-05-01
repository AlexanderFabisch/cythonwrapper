import os
import sys
from contextlib import contextmanager
from pywrap import cython
from pywrap.utils import assert_warns_message

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
