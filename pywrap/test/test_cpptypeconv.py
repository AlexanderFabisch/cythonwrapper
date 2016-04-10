from pywrap.cpptypeconv import (typename, cython_define_basic_inputarg,
                                DoubleArrayTypeConverter, CythonTypeConverter)
from pywrap.parser import Includes
from pywrap.utils import assert_equal_linewise, lines
from nose.tools import assert_equal, assert_in


def test_basic_typename():
    assert_equal(typename("unsigned int"), "unsigned int")


def test_remove_const():
    assert_equal(typename("const int"), "int")


def test_container():
    assert_equal(typename("std::vector<int>"), "vector[int]")


def test_container_of_complex_type():
    assert_equal(typename("std::vector<std::string>"), "vector[string]")


def test_map():
    assert_equal(typename("std::map<std::string, int>"), "map[string, int]")


def test_define_inputarg_basic():
    assert_equal_linewise(
        cython_define_basic_inputarg("int", "cpp_a", "a"),
        "cdef int cpp_a = a")


def test_cython_define_nparray1d_inputarg():
    conv = DoubleArrayTypeConverter("a")
    assert_equal_linewise(
        conv.python_to_cpp(),
        lines("cdef np.ndarray[double, ndim=1] a_array = np.asarray(a)",
              "cdef double * cpp_a = &a_array[0]"""))


def test_add_include_for_cppmodule():
    conv = CythonTypeConverter("Test", "test", "testmodule")
    inc = Includes("thismodule")
    conv.add_includes(inc)
    assert_in("testmodule", inc.cppmodules)
    assert_equal_linewise(
        inc.header(),
        lines("from cython.operator cimport dereference as deref",
              "from _testmodule cimport *",
              "from _thismodule cimport *",
              ""))
