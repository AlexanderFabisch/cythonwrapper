from nose.tools import assert_equal, assert_false, assert_is_instance
from pywrap.testing import cython_extension_from


def test_template_method():
    with cython_extension_from("templatemethod.hpp",
                               custom_config="templatemethodconfig.py"):
        from templatemethod import A
        a = A()
        assert_equal(a.add_one_i(1), 2)
        assert_is_instance(a.add_one_i(1), int)
        assert_equal(a.add_one_d(2.0), 3.0)
        assert_is_instance(a.add_one_d(2.0), float)


def test_missing_specialization():
    with cython_extension_from("templatemethod.hpp", assert_warn=UserWarning,
                               warn_msg="No template specialization"):
        from templatemethod import A
        assert_false(hasattr(A, "add_one"))


def test_template_function():
    with cython_extension_from("templatefunction.hpp",
                               custom_config="templatefunctionconfig.py"):
        from templatefunction import add_one_i, add_one_d
        assert_equal(add_one_i(1), 2)
        assert_is_instance(add_one_i(1), int)
        assert_equal(add_one_d(2.0), 3.0)
        assert_is_instance(add_one_d(2.0), float)


def test_template_class():
    with cython_extension_from("templateclass.hpp",
                               custom_config="templateclassconfig.py"):
        from templateclass import Ai
        a = Ai(5)
        assert_equal(a.get(), 5)
