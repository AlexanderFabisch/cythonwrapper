from pywrap.type_conversion import cythontype_from_cpptype, find_all_subtypes
from nose.tools import assert_equal, assert_in, assert_true


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


def test_find_subtypes_of_primitive():
    subtypes = find_all_subtypes("double")
    assert_true(len(subtypes) == 0)


def test_find_subtypes_of_vector():
    subtypes = find_all_subtypes("vector[double]")
    assert_in("vector", subtypes)
    assert_in("double", subtypes)
    assert_equal(len(subtypes), 2)


def test_find_subtypes_of_complex_hierarchy():
    tname = "type1[type2, type3[type4[type5, type6] ] ]"
    subtypes = find_all_subtypes(tname)
    assert_in("type1", subtypes)
    assert_in("type2", subtypes)
    assert_in("type3", subtypes)
    assert_in("type4", subtypes)
    assert_in("type5", subtypes)
    assert_in("type6", subtypes)
    assert_equal(len(subtypes), 6)
