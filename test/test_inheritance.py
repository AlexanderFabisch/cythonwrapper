from pywrap.testing import cython_extension_from
from nose.tools import assert_equal


def test_independent_parts():
    with cython_extension_from("subclass.hpp"):
        from subclass import A, B
        a = A()
        assert_equal(a.afun(), 1)
        b = B()
        assert_equal(b.afun(), 1)
        assert_equal(b.bfun(), 2)
