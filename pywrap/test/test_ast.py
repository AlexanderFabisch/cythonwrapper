from pywrap.ast import (AST, Enum, Typedef, Function, Clazz, Constructor,
                        Method, Field, Param, TemplateMethod, TemplateClass,
                        TemplateFunction)
from pywrap.utils import lines
from nose.tools import assert_equal, assert_multi_line_equal


def test_empty_ast_string():
    assert_equal(str(AST()), "AST")


def test_ast_string_with_enum():
    ast = AST()
    ast.enums.append(Enum("test.hpp", "", "MyEnum"))
    assert_multi_line_equal(str(ast), lines("AST", "    Enum 'MyEnum'"))


def test_ast_string_with_typedef():
    ast = AST()
    ast.typedefs.append(Typedef("test.hpp", "", "MyTypedef", "double"))
    assert_multi_line_equal(
        str(ast), lines("AST", "    Typedef (double) MyTypedef"))


def test_ast_string_with_function():
    ast = AST()
    ast.functions.append(Function("test.hpp", "", "fun", "void"))
    assert_multi_line_equal(str(ast), lines("AST", "    Function 'fun'"))


def test_ast_string_with_class():
    ast = AST()
    ast.classes.append(Clazz("test.hpp", "bla", "MyClass"))
    assert_multi_line_equal(
        str(ast), lines(
            "AST", "    Class 'MyClass' ('MyClass') (namespace: 'bla')"))


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

    assert_multi_line_equal(
        str(c), lines(
            "Class 'MyClass' ('MyClass')",
            "    Field (bool) my_field",
            "    Constructor '__init__'",
            "        Parameter (double) a",
            "    Method 'my_method'",
            "        Parameter (int) b",
            "        Returns (int)"
        ))


def test_function_string_with_return():
    f = Function("test.hpp", "", "my_fun", "double")
    assert_multi_line_equal(
        str(f), lines(
            "Function 'my_fun'",
            "    Returns (double)"
        )
    )


def test_template_function_string():
    m = TemplateFunction("test.hpp", "", "my_template_fun", "void")
    m.arguments.append(Param("t", "T"))
    m.template_types.append("T")
    assert_multi_line_equal(
        str(m), lines(
            "TemplateFunction 'my_template_fun'",
            "    Parameter (T) t",
            "    Template type 'T'"
        )
    )


def test_template_method_string():
    m = TemplateMethod("my_template_method", "void", "MyClass")
    m.arguments.append(Param("t", "T"))
    m.template_types.append("T")
    assert_multi_line_equal(
        str(m), lines(
            "TemplateMethod 'my_template_method'",
            "    Parameter (T) t",
            "    Template type 'T'"
        )
    )


def test_template_class_string():
    c = TemplateClass("test.hpp", "", "MyTemplateClass")
    c.template_types.append("T")
    assert_multi_line_equal(
        str(c), lines(
            "TemplateClass 'MyTemplateClass' ('MyTemplateClass')",
            "    Template type 'T'"
        )
    )
