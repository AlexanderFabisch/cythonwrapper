from pywrap.type_conversion import cythontype_from_cpptype
from nose.tools import assert_equal


def test_basic_typename():
    assert_equal(cythontype_from_cpptype("unsigned int"), "unsigned int")


def test_remove_const():
    assert_equal(cythontype_from_cpptype("const int"), "int")


def test_container():
    assert_equal(cythontype_from_cpptype("std::vector<int>"),
                 "vector[int]")


def test_container_of_complex_type():
    assert_equal(cythontype_from_cpptype("std::vector<std::string>"),
                 "vector[string]")


def test_map():
    assert_equal(cythontype_from_cpptype("std::map<std::string, int>"),
                 "map[string, int]")


def test_map_str_to_str():
    assert_equal(cythontype_from_cpptype("std::map<std::string, std::string>"),
                 "map[string, string]")

def test_complex_hierarchy():
    tname = ("std::map<std::string, "
             "std::vector<std::map<double, std::string> > >")
    assert_equal(cythontype_from_cpptype(tname),
                 "map[string, vector[map[double, string] ] ]")
