import os
import sys
import numpy as np
from contextlib import contextmanager
from nose.tools import (assert_equal, assert_not_equal, assert_true,
                        assert_false)
from pywrap import cython
from pywrap.utils import assert_warns_message

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


@contextmanager
def cython_extension_from(headers, modulename=None, custom_config=None,
                          cleanup=True):
    if custom_config is not None:
        custom_config = full_paths(custom_config)[0]
    filenames = _write_cython_wrapper(full_paths(headers), modulename,
                                      custom_config)
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


def _write_cython_wrapper(filenames, modulename, custom_config, verbose=0):
    results, cython_files = cython.make_cython_wrapper(
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


def test_twoctors():
    assert_warns_message(UserWarning, "'A' has more than one constructor",
                         cython.make_cython_wrapper, full_paths("twoctors.hpp"),
                         [])


def test_double_in_double_out():
    with cython_extension_from("doubleindoubleout.hpp"):
        from doubleindoubleout import A
        a = A()
        d = 3.213
        assert_equal(d + 2.0, a.plus2(d))


def test_vector():
    with cython_extension_from("vector.hpp"):
        from vector import A
        a = A()
        v = np.array([2.0, 1.0, 3.0])
        n = a.norm(v)
        assert_equal(n, 14.0)


def test_bool_in_bool_out():
    with cython_extension_from("boolinboolout.hpp"):
        from boolinboolout import A
        a = A()
        b = False
        assert_equal(not b, a.neg(b))


def test_string_in_string_out():
    with cython_extension_from("stringinstringout.hpp"):
        from stringinstringout import A
        a = A()
        s = "This is a sentence"
        assert_equal(s + ".", a.end(s))


def test_constructor_args():
    with cython_extension_from("constructorargs.hpp"):
        from constructorargs import A
        a = A(11, 7)
        assert_equal(18, a.sum())


def test_factory():
    with cython_extension_from("factory.hpp"):
        from factory import AFactory
        factory = AFactory()
        a = factory.make()
        assert_equal(5, a.get())


def test_string_vector():
    with cython_extension_from("stringvector.hpp"):
        from stringvector import A
        a = A()
        substrings = ["AB", "CD", "EF"]
        res = a.concat(substrings)
        assert_equal(res, "ABCDEF")


def test_complex_arg():
    with cython_extension_from("complexarg.hpp"):
        from complexarg import A, B
        a = A()
        b = B(a)
        assert_equal(b.get_string(), "test")


def test_complex_ptr_arg():
    with cython_extension_from("complexptrarg.hpp"):
        from complexptrarg import A, B
        a = A()
        b = B(a)
        assert_equal(b.get_string(), "test")


def test_function():
    with cython_extension_from("function.hpp"):
        from function import fun1, fun2
        assert_equal(fun1(0), 0)
        assert_equal(fun2(), 1)

def test_map():
    with cython_extension_from("map.hpp"):
        from map import lookup
        m = {"test": 0}
        assert_equal(lookup(m), 0)


def test_independent_parts():
    with cython_extension_from(["indeppart1.hpp", "indeppart2.hpp"],
                               modulename="combined"):
        from combined import ClassA, ClassB
        a = ClassA()
        assert_false(a.result())
        b = ClassB()
        assert_true(b.result())


def test_dependent_parts():
    with cython_extension_from(["deppart1.hpp", "deppart2.hpp"],
                               modulename="depcombined"):
        from depcombined import A
        a = A()
        b = a.make()
        assert_equal(b.get_value(), 5)


def test_struct():
    with cython_extension_from("mystruct.hpp"):
        from mystruct import A, print_mystruct_a, B, print_mystruct_b
        a = A()
        a.a = 5
        a.b = [1.0, 2.0]
        assert_equal(a.a, 5)
        assert_equal(a.b, [1.0, 2.0])
        assert_equal(print_mystruct_a(a), "a = 5, b[0] = 1, b[1] = 2, ")
        b = B()
        b.a = 10
        assert_equal(b.a, 10)
        assert_equal(print_mystruct_b(b), "a = 10")


def test_operators():
    with cython_extension_from("cppoperators.hpp"):
        from cppoperators import Operators
        op = Operators()
        assert_equal(op(2), 4)
        assert_equal(op[2], 2)
        assert_equal(op + 1, 6)
        assert_equal(op - 1, 4)
        assert_equal(op * 2, 10)
        assert_equal(op / 5, 1)


def test_no_default_constructor():
    with cython_extension_from("nodefaultctor.hpp"):
        from nodefaultctor import A
        a = A()
        a.set_member(5)


def test_typedef():
    with cython_extension_from("typedef.hpp"):
        from typedef import fun
        assert_equal(fun(1.0), 2.0)


def test_complex_field():
    with cython_extension_from("complexfield.hpp"):
        from complexfield import A, B
        a = A()
        a.a = 5
        b = B()
        b.a = a
        b.b = a
        assert_equal(b.a.a, 5)
        assert_equal(b.b.a, 5)


def test_enum():
    with cython_extension_from("enum.hpp"):
        from enum import MyEnum, enum_to_string
        assert_not_equal(MyEnum.FIRSTOPTION, MyEnum.SECONDOPTION)
        assert_not_equal(MyEnum.SECONDOPTION, MyEnum.THIRDOPTION)
        assert_equal(enum_to_string(MyEnum.FIRSTOPTION), "first")
        assert_equal(enum_to_string(MyEnum.SECONDOPTION), "second")
        assert_equal(enum_to_string(MyEnum.THIRDOPTION), "third")


def test_register_custom_type_converter():
    assert_warns_message(UserWarning, "Ignoring method",_write_cython_wrapper,
                         full_paths("boolinboolout.hpp"), None,
                         full_paths("config_register_converter.py")[0])


def test_primitive_pointers():
    with cython_extension_from("primitivepointers.hpp"):
        from primitivepointers import fun1
        assert_equal(fun1(5), 6)


def test_vector_of_struct():
    with cython_extension_from("vectorofstruct.hpp"):
        from vectorofstruct import MyStruct, sum_of_activated_entries
        a = MyStruct()
        a.value = 5
        a.active = False
        b = MyStruct()
        b.value = 10
        b.active = True
        entries = [a, b]
        assert_equal(sum_of_activated_entries(entries), 10)


def test_cstring():
    with cython_extension_from("cstring.hpp"):
        from cstring import length, helloworld
        assert_equal(length("test"), 4)
        assert_equal(helloworld(), "hello world")
