from pywrap.testing import cython_extension_from
from nose.tools import assert_false, assert_true, assert_equal


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


def test_register_custom_type_converter():
    with cython_extension_from("boolinboolout.hpp", assert_warn=UserWarning,
                               warn_msg="Ignoring method",
                               custom_config="config_register_converter.py"):
        pass


def test_another_include_dir():
    with cython_extension_from("addincludedir.hpp",
                               incdirs=["anotherincludedir"]):
        from addincludedir import length
        assert_equal(length(3.0, 4.0), 5.0)
