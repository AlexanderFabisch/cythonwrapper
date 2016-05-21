from pywrap.testing import cython_extension_from
from nose.tools import assert_equal
from pywrap.defaultconfig import Config
from pywrap.testing import full_paths


def test_blacklisted_class():
    config = Config()
    config.ignore_class(full_paths("ignoreclass.hpp")[0], class_name="MyClassA")
    with cython_extension_from("ignoreclass.hpp", config=config,
                               assert_warn=UserWarning, warn_msg="blacklist"):
        pass


def test_blacklisted_method():
    config = Config()
    config.ignore_method(class_name="MyClassB", method_name="myMethod")
    with cython_extension_from("ignoremethod.hpp", config=config,
                               assert_warn=UserWarning, warn_msg="blacklist"):
        pass


def test_abstract_class():
    config = Config()
    config.abstract_class("AbstractClass")
    with cython_extension_from("abstractclass.hpp", config=config,
                               assert_warn=UserWarning, warn_msg="abstract"):
        from abstractclass import AbstractClass, DerivedClass
        d = DerivedClass(5.0)
        a = d.clone()
        assert_equal(a.square(), 25.0)
