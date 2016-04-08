import sys
import os
import contextlib
import warnings
import numpy as np
import pywrap.cython as pycy
from nose.tools import assert_equal


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


PREFIX = os.sep.join(__file__.split(os.sep)[:-1])
SETUPPY_NAME = "setup_test.py"


def full_paths(filenames):
    if isinstance(filenames, str):
        filenames = [filenames]

    if PREFIX == "":
        return filenames
    else:
        attach_prefix = lambda filename: PREFIX + os.sep + filename
        return map(attach_prefix, filenames)


@contextlib.contextmanager
def cython_extension_from(headers):
    filenames = _write_cython_wrapper(full_paths(headers))
    _run_setup()
    try:
        yield
    finally:
        _remove_files(filenames)


def _write_cython_wrapper(filenames, target=".", verbose=0):
    results, cython_files = pycy.make_cython_wrapper(
        filenames, target, verbose)
    results[SETUPPY_NAME] = results["setup.py"]
    del results["setup.py"]
    pycy.write_files(results)
    pycy.cython(cython_files)

    filenames = []
    filenames.extend(results.keys())
    for filename in cython_files:
        filenames.append(filename.replace(pycy.file_ending(filename), "cpp"))
        filenames.append(filename.replace(pycy.file_ending(filename), "so"))
    return filenames


def _run_setup():
    os.system("python %s build_ext -i" % SETUPPY_NAME)


def _remove_files(filenames):
    for f in filenames:
        if os.path.exists(f):
            os.remove(f)


def test_twoctors():
    assert_warns_message(UserWarning, "'A' has more than one constructor",
                         pycy.make_cython_wrapper, full_paths("twoctors.hpp"))


def test_double_in_double_out():
    with cython_extension_from("doubleindoubleout.hpp"):
        from doubleindoubleout import CppA
        a = CppA()
        d = 3.213
        assert_equal(d + 2.0, a.plus2(d))


def test_vector():
    with cython_extension_from("vector.hpp"):
        from vector import CppA
        a = CppA()
        v = np.array([2.0, 1.0, 3.0])
        n = a.norm(v)
        assert_equal(n, 14.0)


def test_bool_in_bool_out():
    with cython_extension_from("boolinboolout.hpp"):
        from boolinboolout import CppA
        a = CppA()
        b = False
        assert_equal(not b, a.neg(b))


def test_string_in_string_out():
    with cython_extension_from("stringinstringout.hpp"):
        from stringinstringout import CppA
        a = CppA()
        s = "This is a sentence"
        assert_equal(s + ".", a.end(s))


def test_constructor_args():
    with cython_extension_from("constructorargs.hpp"):
        from constructorargs import CppA
        a = CppA(11, 7)
        assert_equal(18, a.sum())


def test_factory():
    with cython_extension_from("factory.hpp"):
        from factory import CppAFactory
        factory = CppAFactory()
        a = factory.make()
        assert_equal(5, a.get())


def test_string_vector():
    with cython_extension_from("stringvector.hpp"):
        from stringvector import CppA
        a = CppA()
        substrings = ["AB", "CD", "EF"]
        res = a.concat(substrings)
        assert_equal(res, "ABCDEF")


def test_complex_arg():
    with cython_extension_from("complexarg.hpp"):
        from complexarg import CppA, CppB
        a = CppA()
        b = CppB(a)
        assert_equal(b.get_string(), "test")
