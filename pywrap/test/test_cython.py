import os
from pywrap.cython import make_cython_wrapper
from nose.tools import assert_raises_regexp, assert_false


def test_missing_file():
    assert_raises_regexp(ValueError, "does not exist", make_cython_wrapper,
                         "missing.hpp", [])
    assert_false(os.path.exists("missing.hpp.cc"))


def test_missing_modulename():
    assert_raises_regexp(ValueError, "give a module name", make_cython_wrapper,
                         ["test1.hpp", "test2.hpp"], [], None)


def test_missing_config():
    assert_raises_regexp(ValueError, "Configuration file", make_cython_wrapper,
                         "test.hpp", [], custom_config="doesnotexist.py")


def test_no_header():
    assert_raises_regexp(ValueError, "does not seem to be a header file",
                         make_cython_wrapper, "test.cpp", [])
