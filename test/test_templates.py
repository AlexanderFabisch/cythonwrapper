from nose.tools import assert_equal, assert_false, assert_is_instance
from pywrap.testing import cython_extension_from
from pywrap.defaultconfig import Config


def test_template_method():
    config = Config()
    specs = {
        "A::addOne": [
            ("add_one_i", {"T": "int"}),
            ("add_one_d", {"T": "double"})
        ]
    }
    config.register_method_specialization("A", "addOne", "add_one_i",
                                          {"T": "int"})
    config.register_method_specialization("A", "addOne", "add_one_d",
                                          {"T": "double"})
    with cython_extension_from("templatemethod.hpp", config=config):
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
    config = Config()
    config.register_function_specialization("addOne", "add_one_i", {"T": "int"})
    config.register_function_specialization("addOne", "add_one_d",
                                            {"T": "double"})
    with cython_extension_from("templatefunction.hpp", config=config):
        from templatefunction import add_one_i, add_one_d
        assert_equal(add_one_i(1), 2)
        assert_is_instance(add_one_i(1), int)
        assert_equal(add_one_d(2.0), 3.0)
        assert_is_instance(add_one_d(2.0), float)


def test_template_class():
    config = Config()
    config.register_class_specialization("A", "Ad", {"T": "double"})
    with cython_extension_from("templateclass.hpp", config=config):
        from templateclass import Ad
        a = Ad(5.0)
        assert_equal(a.get(), 5.0)
