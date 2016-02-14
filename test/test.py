import pywrap.cython as pycy
import os
from sklearn.utils.testing import assert_warns_message
from nose.tools import assert_equal
import contextlib


PREFIX = os.sep.join(__file__.split(os.sep)[:-1])


def full_path(filename):
    if PREFIX == "":
        return filename
    else:
        return PREFIX + os.sep + filename


@contextlib.contextmanager
def cython_extension_from(header):
    filenames = _write_cython_wrapper(full_path(header))
    _run_setup()
    try:
        yield
    finally:
        _remove_files(filenames)


def _write_cython_wrapper(filename, target=".", verbose=0):
    results, cython_files = pycy.make_cython_wrapper(filename, target, verbose)
    pycy.write_files(results)
    pycy.cython(cython_files)

    filenames = []
    filenames.extend(results.keys())
    for filename in cython_files:
        filenames.append(filename.replace(pycy._file_ending(filename), "cpp"))
        filenames.append(filename.replace(pycy._file_ending(filename), "so"))
    return filenames


def _run_setup():
    os.system("python setup.py build_ext -i")


def _remove_files(filenames):
    for f in filenames:
        os.remove(f)


def test_twoctors():
    assert_warns_message(UserWarning, "'A' has more than one constructor",
                         pycy.make_cython_wrapper, full_path("twoctors.hpp"))


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
        v = [2.0, 1.0, 3.0]
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
