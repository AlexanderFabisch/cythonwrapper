from pywrap.ast import (AST, Enum, Typedef, Function, Clazz, Constructor,
                        Method, Field, Param)
from pywrap.utils import assert_equal_linewise, lines
from nose.tools import assert_equal


def test_empty_ast_string():
    assert_equal(str(AST()), "AST")


def test_ast_string_with_enum():
    ast = AST()
    ast.enums.append(Enum("test.hpp", "", "MyEnum"))
    assert_equal_linewise(str(ast), lines("AST", "    Enum 'MyEnum'"))


def test_ast_string_with_typedef():
    ast = AST()
    ast.typedefs.append(Typedef("test.hpp", "", "MyTypedef", "double"))
    assert_equal_linewise(
        str(ast), lines("AST", "    Typedef (double) MyTypedef"))


def test_ast_string_with_function():
    ast = AST()
    ast.functions.append(Function("test.hpp", "", "fun", "void"))
    assert_equal_linewise(str(ast), lines("AST", "    Function 'fun'"))


def test_ast_string_with_class():
    ast = AST()
    ast.classes.append(Clazz("test.hpp", "bla", "MyClass"))
    assert_equal_linewise(
        str(ast), lines("AST", "    Class 'MyClass' (namespace: 'bla')"))


def test_class_string_with_members():
    c = Clazz("test.hpp", "", "MyClass")

    ctor = Constructor("MyClass")
    ctor.arguments.append(Param("a", "double"))
    c.constructors.append(ctor)

    method = Method("my_method", "int", "MyClass")
    method.arguments.append(Param("b", "int"))
    c.methods.append(method)

    field = Field("my_field", "bool", "MyClass")
    c.fields.append(field)

    assert_equal_linewise(
        str(c), lines(
            "Class 'MyClass'",
            "    Field (bool) my_field",
            "    Constructor '__init__'",
            "        Parameter (double) a",
            "    Method 'my_method'",
            "        Parameter (int) b",
            "        Returns (int)"
        ))
