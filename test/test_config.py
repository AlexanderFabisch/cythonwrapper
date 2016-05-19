from pywrap.testing import cython_extension_from
from nose.tools import assert_equal


def test_blacklisted_class():
    with cython_extension_from(
            "ignoreclass.hpp", custom_config="ignoreconfig.py",
            assert_warn=UserWarning, warn_msg="blacklist"):
        pass


def test_blacklisted_method():
    with cython_extension_from(
            "ignoremethod.hpp", custom_config="ignoreconfig.py",
            assert_warn=UserWarning, warn_msg="blacklist"):
        pass


def test_abstract_class():
    with cython_extension_from("abstractclass.hpp",
                               custom_config="abstractclassconfig.py",
                               assert_warn=UserWarning, warn_msg="abstract"):
        from abstractclass import AbstractClass, DerivedClass
        d = DerivedClass(5.0)
        a = d.clone()
        assert_equal(a.square(), 25.0)
