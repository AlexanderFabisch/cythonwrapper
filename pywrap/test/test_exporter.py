from pywrap.exporter import (MethodDefinition, SetterDefinition,
                             GetterDefinition, ConstructorDefinition,
                             FunctionDefinition)
from pywrap.cython import TypeInfo
from pywrap.ast import Includes, Param
from pywrap.utils import lines
from pywrap.testing import assert_equal_linewise
from pywrap.defaultconfig import Config
from pywrap.ast import Field


def test_simple_function_def():
    method = MethodDefinition(
        "Testclass", "testfun", [], Includes(),
        "void", TypeInfo({}), Config()).make()
    assert_equal_linewise(
        method,
        lines("cpdef testfun(Testclass self):",
              "    self.thisptr.testfun()")
    )


def test_array_arg_function_def():
    method = MethodDefinition(
        "Testclass", "testfun", [Param("a", "double *"),
                                 Param("aSize", "unsigned int")],
        Includes(), "void", TypeInfo({}), Config()).make()
    assert_equal_linewise(
        method,
        lines("cpdef testfun(Testclass self, np.ndarray[double, ndim=1] a):",
              "    self.thisptr.testfun(&a[0], a.shape[0])")
    )


def test_setter_definition():
    field = Field("myField", "double", "MyClass")
    setter = SetterDefinition(
        "MyClass", field, Includes(), TypeInfo(), Config()).make()
    assert_equal_linewise(
        setter,
        lines(
            "cpdef set_my_field(MyClass self, double myField):",
            "    cdef double cpp_myField = myField",
            "    self.thisptr.myField = cpp_myField"
        )
    )


def test_getter_definition():
    field = Field("myField", "double", "MyClass")
    getter = GetterDefinition(
        "MyClass", field, Includes(), TypeInfo(), Config()).make()
    assert_equal_linewise(
        getter,
        lines(
            "cpdef get_my_field(MyClass self):",
            "    cdef double result = self.thisptr.myField",
            "    return result"
        )
    )

def test_default_ctor_def():
    ctor = ConstructorDefinition("MyClass", [], Includes(), TypeInfo(),
                                 Config(), "MyClass").make()
    assert_equal_linewise(
        ctor,
        lines(
            "def __init__(MyClass self):",
            "    self.thisptr = new cpp.MyClass()"
        )
    )


def test_function_def():
    fun = FunctionDefinition("myFun", [], Includes(), "void", TypeInfo(),
                             Config()).make()
    assert_equal_linewise(
        fun,
        lines(
            "cpdef my_fun():",
            "    cpp.myFun()"
        )
    )
