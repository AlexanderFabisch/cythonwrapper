from pywrap.exporter import MethodDefinition
from pywrap.cython import TypeInfo
from pywrap.parser import Param
from pywrap.ast import Includes, Param
from pywrap.utils import assert_equal_linewise, lines
from pywrap.defaultconfig import Config


def test_simple_function_def():
    assert_equal_linewise(
        MethodDefinition(
            "Testclass", "testfun", [], Includes(),
            "void", TypeInfo({}), Config()).make(),
            lines("cpdef testfun(Testclass self):",
                  "    self.thisptr.testfun()"))


def test_array_arg_function_def():
    testfun = MethodDefinition(
        "Testclass", "testfun", [Param("a", "double *"),
                                 Param("aSize", "unsigned int")],
        Includes(), "void", TypeInfo({}), Config()).make()
    assert_equal_linewise(testfun,
        lines("cpdef testfun(Testclass self, np.ndarray[double, ndim=1] a):",
              "    self.thisptr.testfun(&a[0], a.shape[0])"))
