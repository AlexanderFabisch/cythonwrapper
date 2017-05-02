from pywrap.testing import cython_extension_from
from nose.tools import assert_equal, assert_not_equal


def test_namespaces():
    with cython_extension_from("namespaces.hpp"):
        from namespaces import ClassA, ClassB


def test_constructor_args():
    with cython_extension_from("constructorargs.hpp"):
        from constructorargs import A
        a = A(11, 7)
        assert_equal(18, a.sum())


def test_function():
    with cython_extension_from("function.hpp"):
        from function import fun1, fun2
        assert_equal(fun1(0), 0)
        assert_equal(fun2(), 1)


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
        assert_equal(op % 2, 1)
        assert_equal(op and True, True)
        op += 3
        assert_equal(op.v, 3)
        op -= 1
        assert_equal(op.v, 2)
        op *= 2
        assert_equal(op.v, 4)
        op /= 4
        assert_equal(op.v, 1)
        op %= 2
        assert_equal(op.v, 1)
        op |= True
        assert_equal(op.b, True)
        op &= True
        assert_equal(op.b, True)


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


def test_enum_in_class():
    with cython_extension_from("enuminclass.hpp"):
        from enuminclass import MyEnum, enum_to_string
        assert_not_equal(MyEnum.FIRSTOPTION, MyEnum.SECONDOPTION)
        assert_not_equal(MyEnum.SECONDOPTION, MyEnum.THIRDOPTION)
        assert_equal(enum_to_string(MyEnum.FIRSTOPTION), "first")
        assert_equal(enum_to_string(MyEnum.SECONDOPTION), "second")
        assert_equal(enum_to_string(MyEnum.THIRDOPTION), "third")


def test_class_in_class():
    with cython_extension_from("classinclass.hpp"):
        from classinclass import ClassB, mystatfun
        b = ClassB()
        assert_equal(b.myfun(), 123)
        assert_equal(mystatfun(), 124)


def test_static_method():
    with cython_extension_from("staticmethod.hpp"):
        from staticmethod import plus1, plus2
        assert_equal(plus1(1), 2)
        assert_equal(plus2(1), 3)
