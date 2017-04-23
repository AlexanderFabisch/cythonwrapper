from pywrap.testing import cython_extension_from
from nose.tools import assert_equal


def test_overloading_method_is_not_possible():
    with cython_extension_from(
            "overloadmethod.hpp", assert_warn=UserWarning,
            warn_msg="Method 'A.plusOne' is already defined"):
        from overloadmethod import A
        a = A()
        assert_equal(a.plus_one(3.0), 4.0)


def test_overloading_function_is_not_possible():
    with cython_extension_from(
            "overloadfunction.hpp", assert_warn=UserWarning,
            warn_msg="Function 'plusOne' is already defined"):
        from overloadfunction import plus_one
        assert_equal(plus_one(3.0), 4.0)