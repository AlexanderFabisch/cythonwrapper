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
    parser = Parser("test.hpp", None, Includes())
    parser.init_ast()
    parser.add_typedef("double", "tdef")
    assert_equal(len(parser.ast.typedefs), 1)


def test_distributed_struct():
    parser = Parser("test.hpp", None, Includes())
    parser.init_ast()
    parser.add_struct_decl("")
    assert_is_not_none(parser.ast.unnamed_struct)
    parser.add_typedef("struct mystruct", "mystruct")
    assert_is_none(parser.unnamed_struct)
    assert_equal(len(parser.ast.classes), 1)


def test_struct():
    parser = Parser("test.hpp", None, Includes())
    parser.init_ast()
    parser.add_struct_decl("MyStruct")
    assert_equal(len(parser.ast.classes), 1)


def test_add_function():
    parser = Parser("test.hpp", None, Includes())
    parser.init_ast()
    parser.add_function("myFun", "void", "")
    assert_equal(len(parser.ast.functions), 1)


def test_add_class_with_field_ctor_and_method():
    parser = Parser("test.hpp", None, Includes())
    parser.init_ast()
    parser.add_class("MyClass")
    assert_equal(len(parser.ast.classes), 1)
    parser.add_ctor()
    assert_equal(len(parser.ast.classes[0].constructors), 1)
    parser.add_param("a", "int")
    assert_equal(len(parser.ast.classes[0].constructors[0].arguments), 1)
    parser.add_method("myMethod", "int")
    assert_equal(len(parser.ast.classes[0].methods), 1)
    parser.add_field("b", "bool")
    assert_equal(len(parser.ast.classes[0].fields), 1)


def test_add_argument_without_method():
    parser = Parser("test.hpp", None, Includes())
    parser.init_ast()
    assert_warns_message(UserWarning, "Ignored function parameter",
                         parser.add_param, "a", "void")
