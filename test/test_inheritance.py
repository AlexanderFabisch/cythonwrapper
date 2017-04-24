from pywrap.testing import cython_extension_from
from nose.tools import assert_equal


def test_ambiguous_method():
    with cython_extension_from("subclass.hpp"):
        from subclass import A, B
        a = A()
        assert_equal(a.afun(), 1)
        b = B()
        assert_equal(b.afun(), 1)
        assert_equal(b.bfun(), 2)


def test_complex_hierarchy():
    with cython_extension_from("complexhierarchy.hpp"):
        from complexhierarchy import A, B
        a = A()
        assert_equal(a.base1_method(), 1)
        assert_equal(a.base2_method(), 2)
        assert_equal(a.a_method(), 3)
        b = B()
        assert_equal(b.base1_method(), 4)
        assert_equal(b.base2_method(), 2)
        assert_equal(b.b_method(), 5)


def test_inheritance_with_namespace():
    with cython_extension_from("inheritancewithnamespace.hpp"):
        from inheritancewithnamespace import ClassA, ClassB
        a = ClassA()
        assert_equal(a.method_a(), 1)
        b = ClassB()
        assert_equal(b.method_a(), 1)
        assert_equal(b.method_b(), 2)
