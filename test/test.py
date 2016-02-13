import pywrap.cython as pycy
import os
from sklearn.utils.testing import assert_warns_message
from nose.tools import assert_equal


PREFIX = os.sep.join(__file__.split(os.sep)[:-1])


def full_path(filename):
    if PREFIX == "":
        return filename
    else:
        return PREFIX + os.sep + filename


def write_cython_wrapper(filename, target=".", verbose=0):
    results, cython_files = pycy.make_cython_wrapper(filename, target, verbose)
    pycy.write_files(results)
    pycy.cython(cython_files)

    filenames = []
    filenames.extend(results.keys())
    for filename in cython_files:
        filenames.append(filename.replace(pycy._file_ending(filename), "cpp"))
        filenames.append(filename.replace(pycy._file_ending(filename), "so"))
    return filenames


def run_setup():
    os.system("python setup.py build_ext -i")


def remove_files(filenames):
    for f in filenames:
        os.remove(f)


def test_twoctors():
    assert_warns_message(UserWarning, "'A' has more than one constructor",
                         pycy.make_cython_wrapper, full_path("twoctors.hpp"))


def test_double_in_double_out():
    filenames = write_cython_wrapper("doubleindoubleout.hpp")
    run_setup()

    from doubleindoubleout import CppA
    a = CppA()
    d = 3.213
    assert_equal(d + 2.0, a.plus2(d))

    remove_files(filenames)


def test_vector():
    filenames = write_cython_wrapper("vector.hpp")
    run_setup()

    from vector import CppA
    a = CppA()
    v = [2.0, 1.0, 3.0]
    n = a.norm(v)
    assert_equal(n, 14.0)

    remove_files(filenames)


def test_bool_in_bool_out():
    filenames = write_cython_wrapper("boolinboolout.hpp")
    run_setup()

    from boolinboolout import CppA
    a = CppA()
    b = False
    assert_equal(not b, a.neg(b))

    remove_files(filenames)


def test_string_in_string_out():
    filenames = write_cython_wrapper("stringinstringout.hpp")
    run_setup()

    from stringinstringout import CppA
    a = CppA()
    s = "This is a sentence"
    assert_equal(s + ".", a.end(s))

    remove_files(filenames)
