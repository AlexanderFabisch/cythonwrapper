from pywrap.ast import (Ast, Enum, Typedef, Function, Clazz, Constructor,
                        Method, Field, Param, TemplateMethod, TemplateClass,
                        TemplateFunction)
from pywrap.utils import lines
from nose.tools import assert_equal, assert_multi_line_equal


def test_empty_ast_string():
    assert_equal(str(Ast()), "AST")


def test_ast_string_with_enum():
    ast = Ast()
    ast.nodes.append(Enum("test.hpp", "", "MyEnum"))
    assert_multi_line_equal(str(ast), lines("AST", "    Enum 'MyEnum'"))


def test_ast_string_with_typedef():
    ast = Ast()
    ast.nodes.append(Typedef("test.hpp", "", "MyTypedef", "double"))
    assert_multi_line_equal(
        str(ast), lines("AST", "    Typedef (double) MyTypedef"))


def test_ast_string_with_function():
    ast = Ast()
    ast.nodes.append(Function("test.hpp", "", "fun", "void"))
    assert_multi_line_equal(str(ast), lines("AST", "    Function 'fun'"))


def test_ast_string_with_class():
    ast = Ast()
    ast.nodes.append(Clazz("test.hpp", "bla", "MyClass"))
    assert_multi_line_equal(
        str(ast), lines(
            "AST", "    Class 'MyClass' ('MyClass') (namespace: 'bla')"))


def test_class_string_with_members():
    c = Clazz("test.hpp", "", "MyClass")

    ctor = Constructor("MyClass")
    ctor.nodes.append(Param("a", "double"))
    c.nodes.append(ctor)

    method = Method("my_method", "int", "MyClass")
    method.nodes.append(Param("b", "int"))
    c.nodes.append(method)

    field = Field("my_field", "bool", "MyClass")
    c.nodes.append(field)

    assert_multi_line_equal(
        str(c), lines(
            "Class 'MyClass' ('MyClass')",
            "    Constructor '__init__'",
            "        Parameter (double) a",
            "    Method 'my_method'",
            "        Parameter (int) b",
            "        Returns (int)",
            "    Field (bool) my_field"
        ))


def test_class_string_with_base_class():
    c = Clazz("test.hpp", "", "MyClass")
    c.base = "MyBase"
    assert_equal(str(c), "Class 'MyClass' ('MyClass') extends 'MyBase'")


def test_class_fullname():
    c = Clazz("test.hpp", "Namespace", "MyClass")
    assert_equal(c.fullname(), "Namespace::MyClass")


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
    m.nodes.append(Param("t", "T"))
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
    m.nodes.append(Param("t", "T"))
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


def test_walk_through_ast():
    ast = Ast()

    c = Clazz("test.hpp", "", "MyClass")
    ctor = Constructor("MyClass")
    ctor.nodes.append(Param("a", "double"))
    c.nodes.append(ctor)
    method = Method("my_method", "int", "MyClass")
    method.nodes.append(Param("b", "int"))
    c.nodes.append(method)
    field = Field("my_field", "bool", "MyClass")
    c.nodes.append(field)
    ast.nodes.append(c)

    function = Function("test.hpp", "", "fun", "void")
    param = Param("a", "double")
    function.nodes.append(param)
    ast.nodes.append(function)

    typedef = Typedef("test.hpp", "", "myfloat", "double")
    ast.nodes.append(typedef)

    enum = Enum("test.hpp", "", "MyEnum")
    ast.nodes.append(enum)

    class CountingExporter:
        def __getattr__(self, name):
            parts = name.split("_")
            if parts[0] != "visit":
                raise AttributeError(name)
            element = "_".join(parts[1:])
            counter_name = element + "_count"
            if not hasattr(self, counter_name):
                setattr(self, counter_name, 0)
            def count_element(_):
                previous_value = getattr(self, counter_name)
                setattr(self, counter_name, previous_value + 1)
            return count_element

    exporter = CountingExporter()
    ast.accept(exporter)
    assert_equal(exporter.ast_count, 1)
    assert_equal(exporter.clazz_count, 1)
    assert_equal(exporter.constructor_count, 1)
    assert_equal(exporter.method_count, 1)
    assert_equal(exporter.field_count, 1)
    assert_equal(exporter.function_count, 1)
    assert_equal(exporter.typedef_count, 1)
    assert_equal(exporter.enum_count, 1)


def test_param_with_default():
    param = Param("a", "double")
    param.default_value = "5.0"
    assert_equal(str(param), "Parameter (double) a = 5.0")
