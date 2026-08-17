import os
from pywrap.cython import make_cython_wrapper, load_config
from pywrap.parser import TypeInfo
from nose.tools import (assert_raises_regexp, assert_false, assert_equal,
                        assert_is_not_none)


def test_missing_file():
    assert_raises_regexp(ValueError, "does not exist", make_cython_wrapper,
                         "missing.hpp", [])
    assert_false(os.path.exists("missing.hpp.cc"))


def test_missing_modulename():
    assert_raises_regexp(ValueError, "give a module name", make_cython_wrapper,
                         ["test1.hpp", "test2.hpp"], [], None)


def test_load_config():
    configfile = "customconfigasd.py"
    with open(configfile, "w") as f:
        f.write("""
from pywrap.defaultconfig import Config

config = Config()
config.add_declaration("mymodule", "asd")
""")
    try:
        config = load_config(configfile)
        assert_equal(config.additional_declarations["mymodule"], "asd")
    finally:
        os.remove(configfile)


def test_load_default_config():
    config = load_config(None)
    assert_is_not_none(config)


def test_missing_config():
    assert_raises_regexp(ValueError, "Configuration file", load_config,
                         "doesnotexist.py")


def test_no_header():
    assert_raises_regexp(ValueError, "does not seem to be a header file",
                         make_cython_wrapper, "test.cpp", [])

def test_underlying_type():
    assert_equal(TypeInfo().underlying_type("tdef"), "tdef")
    assert_equal(TypeInfo(typedefs={"tdef": "float"}).underlying_type("tdef"),
                 "float")


def test_missing_incdir():
    assert_raises_regexp(ValueError, "Include directory", make_cython_wrapper,
                         "test.hpp", [], incdirs=["/doesnotexist"])
