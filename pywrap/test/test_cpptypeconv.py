from pywrap.type_conversion import typename, cython_define_basic_inputarg
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


def test_map():
    assert_equal(typename("std::map<std::string, int>"), "map[string, int]")


def test_map_str_to_str():
    assert_equal(typename("std::map<std::string, std::string>"),
                 "map[string, string]")

def test_complex_hierarchy():
    tname = ("std::map<std::string, "
             "std::vector<std::map<double, std::string> > >")
    assert_equal(typename(tname), "map[string, vector[map[double, string] ] ]")


def test_define_inputarg_basic():
    assert_equal_linewise(
        cython_define_basic_inputarg("int", "cpp_a", "a"), "int cpp_a = a")
