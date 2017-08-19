from pywrap.libclang import find_clang, SUPPORTED_VERSIONS
from nose.tools import assert_in


def test_find_clang():
    CLANG_VERSION, CLANG_INCDIR = find_clang(set_library_path=False, verbose=2)
    assert_in(CLANG_VERSION, SUPPORTED_VERSIONS)