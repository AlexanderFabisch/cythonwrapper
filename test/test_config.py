import os
import shutil
from pywrap.testing import cython_extension_from
from nose.tools import assert_equal
from pywrap.defaultconfig import Config
from pywrap.testing import full_paths
from pywrap.utils import hidden_stdout


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


def test_external_library():
    library_dir = full_paths("externallib")[0]
    cwd = os.getcwd()
    try:
        os.chdir(library_dir)
        with hidden_stdout():
            os.system("make")
    finally:
        os.chdir(cwd)

    shutil.copyfile(os.path.join(library_dir, "libmylib.so"), "libmylib.so")

    config = Config()
    config.add_library_dir(library_dir)
    config.add_library("mylib")
    with cython_extension_from("withexternallib.hpp", config=config,
                               incdirs=["externallib"]):
        try:
            from withexternallib import get_number
            assert_equal(get_number(), 5)
        finally:
            os.remove("libmylib.so")
