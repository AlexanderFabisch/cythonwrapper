import os
from pywrap.cython import make_cython_wrapper
from nose.tools import assert_raises, assert_false


def test_missing_file():
    assert_raises(ValueError, make_cython_wrapper, "missing.hpp", [])
    assert_false(os.path.exists("missing.hpp.cc"))


def test_missing_modulename():
    assert_raises(ValueError, make_cython_wrapper,
                  ["test1.hpp", "test2.hpp"], [], None)


def test_missing_config():
    assert_raises(ValueError, make_cython_wrapper,
                  "test.hpp", [], custom_config="doesnotexist.py")


def test_no_header():
    assert_raises(ValueError, make_cython_wrapper, "test.cpp", [])
