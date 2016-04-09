from pywrap.cpptypeconv import (typename, cython_define_basic_inputarg,
                                cython_define_nparray1d_inputarg)
from pywrap.utils import assert_equal_linewise
from nose.tools import assert_equal


def test_basic_typename():
    assert_equal(typename("unsigned int"), "unsigned int")


def test_remove_const():
    assert_equal(typename("const int"), "int")


def test_container():
    assert_equal(typename("std::vector<int>"), "vector[int]")


def test_container_of_complex_type():
    assert_equal(typename("std::vector<std::string>"), "vector[string]")


def test_define_inputarg_basic():
    assert_equal_linewise(
        cython_define_basic_inputarg("int", "cpp_a", "a"),
        "cdef int cpp_a = a")


def test_cython_define_nparray1d_inputarg():
    assert_equal_linewise(
        cython_define_nparray1d_inputarg("double *", "cpp_a", "a"),
        """cdef np.ndarray[double, ndim=1] a_array = np.asarray(a)
cdef double * cpp_a = &a_array[0]""")
