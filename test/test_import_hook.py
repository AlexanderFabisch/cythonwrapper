import sys
from pywrap.import_hook import CppFinder
from pywrap.testing import PREFIX
from pywrap.utils import remove_files
from nose.tools import assert_equal, assert_raises


def test_import_hook_missing_header():
    sys.meta_path.append(CppFinder(import_path=PREFIX))
    assert_raises(ImportError, __import__, "missing")


def test_import_hook():
    sys.meta_path.append(CppFinder(import_path=PREFIX))
    try:
        import doubleindoubleout
        a = doubleindoubleout.A()
        assert_equal(a.plus2(2.0), 4.0)
    finally:
        remove_files(["doubleindoubleout.so"])
