import os
import tempfile
from pywrap.parser import Parser
from pywrap.ast import Includes
from nose.tools import (assert_true, assert_equal, assert_is_not_none,
                        assert_is_none)
from pywrap.testing import assert_warns_message


def test_include_string():
    inc = Includes()
    inc.add_include_for("string")
    assert_true(inc.stl["string"])


def test_include_map():
    inc = Includes()
    inc.add_include_for("map[string, int]")
    assert_true(inc.stl["map"])
    assert_true(inc.stl["string"])


def test_add_typedef():
    parser = Parser("test.hpp")
    parser.init_ast()
    parser.add_typedef("double", "tdef")
    assert_equal(len(parser.ast.nodes), 1)


def test_distributed_struct():
    parser = Parser("test.hpp")
    parser.init_ast()
    parser.add_struct_decl("")
    assert_is_not_none(parser.ast.unnamed_struct)
    parser.add_typedef("struct mystruct", "mystruct")
    assert_is_none(parser.unnamed_struct)
    assert_equal(len(parser.ast.nodes), 1)


def test_struct():
    parser = Parser("test.hpp")
    parser.init_ast()
    parser.add_struct_decl("MyStruct")
    assert_equal(len(parser.ast.nodes), 1)


def test_add_function():
    parser = Parser("test.hpp")
    parser.init_ast()
    parser.add_function("myFun", "void", "")
    assert_equal(len(parser.ast.nodes), 1)


def test_add_class_with_field_ctor_and_method():
    parser = Parser("test.hpp")
    parser.init_ast()
    parser.add_class("MyClass")
    assert_equal(len(parser.ast.nodes), 1)
    parser.add_ctor()
    assert_equal(len(parser.ast.nodes[0].constructors), 1)
    parser.add_param("a", "int")
    assert_equal(len(parser.ast.nodes[0].constructors[0].arguments), 1)
    parser.add_method("myMethod", "int")
    assert_equal(len(parser.ast.nodes[0].methods), 1)
    parser.add_field("b", "bool")
    assert_equal(len(parser.ast.nodes[0].fields), 1)


def test_add_argument_without_method():
    parser = Parser("test.hpp")
    parser.init_ast()
    assert_warns_message(UserWarning, "Ignored function parameter",
                         parser.add_param, "a", "void")


def test_add_template_function():
    parser = Parser("test.hpp")
    parser.init_ast()
    parser.add_template_function("myFun", "void")
    assert_equal(len(parser.ast.nodes), 1)
    parser.add_template_type("T")
    assert_equal(len(parser.ast.nodes[0].template_types), 1)


def test_add_template_class():
    parser = Parser("test.hpp")
    parser.init_ast()
    parser.add_template_class("MyTemplateClass")
    assert_equal(len(parser.ast.nodes), 1)
    parser.add_template_type("T")
    assert_equal(len(parser.ast.nodes[0].template_types), 1)
    parser.add_ctor()
    assert_equal(len(parser.ast.nodes[0].constructors), 1)
    parser.add_param("a", "T")
    assert_equal(len(parser.ast.nodes[0].constructors[0].arguments), 1)
    parser.add_method("myMethod", "int")
    assert_equal(len(parser.ast.nodes[0].methods), 1)
    parser.add_field("b", "bool")
    assert_equal(len(parser.ast.nodes[0].fields), 1)


def test_add_template_method():
    parser = Parser("test.hpp")
    parser.init_ast()
    parser.add_class("MyClass")
    assert_equal(len(parser.ast.nodes), 1)
    parser.add_ctor()
    assert_equal(len(parser.ast.nodes[0].constructors), 1)
    parser.add_param("a", "int")
    assert_equal(len(parser.ast.nodes[0].constructors[0].arguments), 1)
    parser.add_template_method("myMethod", "T")
    assert_equal(len(parser.ast.nodes[0].methods), 1)
    parser.add_template_type("T")
    assert_equal(len(parser.ast.nodes[0].methods[0].template_types[0]), 1)
    parser.add_field("b", "T")
    assert_equal(len(parser.ast.nodes[0].fields), 1)


def test_parse_file():
    testcode = """
typedef double myfloat;
enum E
{
    E1, E2
};

class A
{
public:
    int i;
    myfloat d;
    bool b;
    A(int i=1, double d=1.0, bool b=false) {}
    void method1(int i) {}
    double method2(bool b) {}
};

struct B
{
    int i;
};

template<typename T1>
class C
{
public:
    C(T t) {}
    template<typename T2>
    void method(T2 t) {}
};

void function1() {}

namespace N1
{
namespace N2
{
template<typename T>
void function2() {}
}
}
"""

    _, filename = tempfile.mkstemp(".hpp")
    with open(filename, "w") as f:
        f.write(testcode)

    try:
        parser = Parser(filename)
        ast = parser.parse()
    finally:
        if os.path.exists(filename):
            os.remove(filename)
        if os.path.exists(filename + ".cc"):
            os.remove(filename + ".cc")

    assert_equal(len(ast.nodes), 3 + 2 + 1 + 1)
