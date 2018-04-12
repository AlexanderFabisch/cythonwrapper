from pywrap.libclang import find_clang
from nose.tools import assert_in


def test_find_clang():
    CLANG_VERSION, CLANG_INCDIR = find_clang(set_library_path=False, verbose=2)
    assert_in(CLANG_VERSION, ["3.5", "3.6", "3.7", "3.8", "3.9", "4.0", "5.0", "6.0"])
