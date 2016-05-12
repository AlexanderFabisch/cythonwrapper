from pywrap.defaultconfig import Config
from pywrap.template_specialization import FunctionSpecializer
from pywrap.ast import TemplateFunction
from nose.tools import assert_equal


def test_function_specializer():
    config = Config()
    config.register_function_specialization("myFun", "myFunInt",
                                            {"T": "int"})
    specializer = FunctionSpecializer(config)
    template = TemplateFunction("test.hpp", "", "myFun", "T")
    functions = specializer.specialize(template)
    assert_equal(len(functions), 1)
    function = functions[0]
    assert_equal(function.name, "myFunInt")
    assert_equal(function.result_type, "int")
