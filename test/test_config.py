from pywrap.testing import cython_extension_from


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
