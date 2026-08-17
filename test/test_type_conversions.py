import numpy as np
from pywrap.testing import cython_extension_from
from nose.tools import assert_equal, assert_raises


def test_bool_in_bool_out():
    with cython_extension_from("boolinboolout.hpp"):
        from boolinboolout import A
        a = A()
        b = False
        assert_equal(not b, a.neg(b))


def test_double_in_double_out():
    with cython_extension_from("doubleindoubleout.hpp"):
        from doubleindoubleout import A
        a = A()
        d = 3.213
        assert_equal(d + 2.0, a.plus2(d))


def test_complex_arg():
    with cython_extension_from("complexarg.hpp"):
        from complexarg import A, B
        a = A()
        b = B(a)
        assert_equal(b.get_string(), "test")


def test_map():
    with cython_extension_from("maparg.hpp"):
        from maparg import lookup
        m = {"test": 0}
        assert_equal(lookup(m), 0)


def test_vector():
    with cython_extension_from("vector.hpp"):
        from vector import A
        a = A()
        v = np.array([2.0, 1.0, 3.0])
        n = a.norm(v)
        assert_equal(n, 14.0)


def test_string_in_string_out():
    with cython_extension_from("stringinstringout.hpp"):
        from stringinstringout import A
        a = A()
        s = "This is a sentence"
        assert_equal(s + ".", a.end(s))


def test_string_vector():
    with cython_extension_from("stringvector.hpp"):
        from stringvector import A
        a = A()
        substrings = ["AB", "CD", "EF"]
        res = a.concat(substrings)
        assert_equal(res, "ABCDEF")


def test_complex_ptr_arg():
    with cython_extension_from("complexptrarg.hpp"):
        from complexptrarg import A, B
        a = A()
        b = B(a)
        assert_equal(b.get_string(), "test")


def test_factory():
    with cython_extension_from("factory.hpp"):
        from factory import AFactory
        factory = AFactory()
        a = factory.make()
        assert_equal(5, a.get())


def test_primitive_pointers():
    with cython_extension_from("primitivepointers.hpp"):
        from primitivepointers import fun1
        assert_equal(fun1(5), 6)


def test_cstring():
    with cython_extension_from("cstring.hpp"):
        from cstring import length, helloworld
        assert_equal(length("test"), 4)
        assert_equal(helloworld(), "hello world")


def test_fixed_length_array():
    with cython_extension_from("fixedarray.hpp"):
        from fixedarray import to_string
        assert_equal(to_string([1, 2, 3, 4, 5]), "[1, 2, 3, 4, 5]")
        assert_raises(ValueError, to_string, [1, 2, 3, 4])
        assert_raises(TypeError, to_string, [1, 2, 3, 4, "a"])


def test_missing_default_ctor():
    with cython_extension_from("missingdefaultctor.hpp", hide_errors=True):
        assert_raises(ImportError, __import__, "missingdefaultctor")


def test_missing_assignment():
    with cython_extension_from("missingassignmentop.hpp", hide_errors=True):
        assert_raises(ImportError, __import__, "missingassignmentop")


def test_exceptions():
    # A list of convertible exceptions can be found in the Cython docs:
    # http://docs.cython.org/src/userguide/wrapping_CPlusPlus.html#exceptions
    with cython_extension_from("throwexception.hpp"):
        from throwexception import (throw_bad_alloc, throw_bad_cast,
                                    throw_domain_error, throw_invalid_argument,
                                    throw_ios_base_failure,
                                    throw_out_of_range, throw_overflow_error,
                                    throw_range_error, throw_underflow_error,
                                    throw_other)
        assert_raises(MemoryError, throw_bad_alloc)
        assert_raises(TypeError, throw_bad_cast)
        assert_raises(ValueError, throw_domain_error)
        assert_raises(ValueError, throw_invalid_argument)
        assert_raises(IOError, throw_ios_base_failure)
        assert_raises(IndexError, throw_out_of_range)
        assert_raises(OverflowError, throw_overflow_error)
        assert_raises(ArithmeticError, throw_range_error)
        assert_raises(ArithmeticError, throw_underflow_error)
        assert_raises(RuntimeError, throw_other)
