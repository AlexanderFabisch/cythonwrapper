from pywrap.defaultconfig import Config
from pywrap.template_specialization import (FunctionSpecializer,
                                            ClassSpecializer, MethodSpecializer)
from pywrap.ast import Param, TemplateFunction, TemplateClass, TemplateMethod
from nose.tools import assert_equal
from pywrap.testing import assert_warns_message


def test_missing_template_specialization():
    config = Config()
    specializer = FunctionSpecializer(config)

    template = TemplateFunction("test.hpp", "", "myFun", "T")
    template.template_types.append("T")

    assert_warns_message(UserWarning, "No template specialization registered",
                         specializer.specialize, template)


def test_function_specializer():
    config = Config()
    config.register_function_specialization("MyNamespace::myFun", "myFunInt",
                                            {"T": "int"})
    config.register_function_specialization("MyNamespace::myFun", "myFunDouble",
                                            {"T": "double"})
    specializer = FunctionSpecializer(config)

    template = TemplateFunction("test.hpp", "MyNamespace", "myFun", "T")
    template.arguments.append(Param("a", "T"))
    template.template_types.append("T")

    functions = specializer.specialize(template)
    assert_equal(len(functions), 2)
    assert_equal(functions[0].name, "myFunInt")
    assert_equal(functions[0].result_type, "int")
    assert_equal(len(functions[0].arguments), 1)
    assert_equal(functions[0].arguments[0].tipe, "int")
    assert_equal(functions[1].name, "myFunDouble")
    assert_equal(functions[1].result_type, "double")
    assert_equal(len(functions[1].arguments), 1)
    assert_equal(functions[1].arguments[0].tipe, "double")


def test_class_specializer():
    config = Config()
    config.register_class_specialization("MyClass", "MyClassDouble",
                                         {"T": "double"})
    specializer = ClassSpecializer(config)

    template = TemplateClass("test.hpp", "", "MyClass")
    template.template_types.append("T")

    classes = specializer.specialize(template)
    assert_equal(len(classes), 1)
    clazz = classes[0]
    assert_equal(clazz.name, "MyClassDouble")
    assert_equal(clazz.get_cppname(), "MyClass[double]")
    assert_equal(clazz.get_attached_typeinfo(), {"T": "double"})


def test_method_specialization():
    config = Config()
    config.register_method_specialization("MyClass", "myMethod", "my_method_b",
                                          {"T": "bool"})
    specializer = MethodSpecializer(config)

    template = TemplateMethod("myMethod", "T", "MyClass")
    template.arguments.append(Param("a", "T"))
    template.template_types.append("T")

    methods = specializer.specialize(template)
    assert_equal(len(methods), 1)
    method = methods[0]
    assert_equal(method.name, "my_method_b")
    assert_equal(method.result_type, "bool")
    assert_equal(len(method.arguments), 1)
    assert_equal(method.arguments[0].tipe, "bool")
