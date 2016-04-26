from pywrap.defaultconfig import Config
from nose.tools import assert_equal, assert_raises


def test_cpp_operator():
    config = Config()
    assert_equal(config.cpp_to_py_operator("operator()"), "__call__")
    assert_raises(NotImplementedError, config.cpp_to_py_operator, "operator<<")