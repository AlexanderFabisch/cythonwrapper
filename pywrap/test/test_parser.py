from pywrap.parser import (AST, add_function, add_class, add_field, add_ctor,
                           add_method, add_param, add_typedef, add_struct_decl)
from pywrap.ast import Includes
from nose.tools import (assert_true, assert_equal, assert_is_not_none,
                        assert_is_none)
from pywrap.utils import assert_warns_message


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
    ast = AST(Includes(), "test.hpp")
    add_typedef(ast, "double", "tdef")
    assert_equal(len(ast.typedefs), 1)


def test_distributed_struct():
    ast = AST(Includes(), "test.hpp")
    add_struct_decl(ast, "")
    assert_is_not_none(ast.unnamed_struct)
    add_typedef(ast, "struct mystruct", "mystruct")
    assert_is_none(ast.unnamed_struct)
    assert_equal(len(ast.classes), 1)


def test_struct():
    ast = AST(Includes(), "test.hpp")
    add_struct_decl(ast, "MyStruct")
    assert_equal(len(ast.classes), 1)


def test_add_function():
    ast = AST(Includes(), "test.hpp")
    add_function(ast, "myFun", "void")
    assert_equal(len(ast.functions), 1)


def test_add_class_with_field_ctor_and_method():
    ast = AST(Includes(), "test.hpp")
    add_class(ast, "MyClass")
    assert_equal(len(ast.classes), 1)
    add_ctor(ast)
    assert_equal(len(ast.classes[0].constructors), 1)
    add_param(ast, "a", "int")
    assert_equal(len(ast.classes[0].constructors[0].arguments), 1)
    add_method(ast, "myMethod", "int")
    assert_equal(len(ast.classes[0].methods), 1)
    add_field(ast, "b", "bool")
    assert_equal(len(ast.classes[0].fields), 1)


def test_add_argument_without_method():
    ast = AST(Includes(), "test.hpp")
    assert_warns_message(UserWarning, "Ignored function parameter", add_param,
                         ast, "a", "void")
