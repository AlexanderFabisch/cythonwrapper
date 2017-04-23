from pywrap.testing import cython_extension_from
from nose.tools import assert_equal


def test_overloading_method_is_not_possible():
    with cython_extension_from("sgetternameclash.hpp"):
        from sgetternameclash import A
        a = A()
        a.n = 20
        assert_equal(a.n, 20)
        a.set_n(30)
        assert_equal(a.get_n(), 30)