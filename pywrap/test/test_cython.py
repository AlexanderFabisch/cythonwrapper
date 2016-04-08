from pywrap.exporter import FunctionDefinition
from pywrap.parser import Includes, Param
from pywrap.utils import assert_equal_linewise


def test_simple_function_def():
    assert_equal_linewise(
        FunctionDefinition(
            "testfun", [], Includes("test_module"),
            initial_args=["self"], result_type="void").make(),
        """def testfun(self):
    self.thisptr.testfun()
""")


def test_array_arg_function_def():
    testfun = FunctionDefinition(
        "testfun", [Param("a", "double *"), Param("aSize", "unsigned int")],
        Includes("test_module"), initial_args=["self"], result_type="void"
        ).make()
    assert_equal_linewise(testfun,
        """def testfun(self, a):
    cdef np.ndarray[double, ndim=1] a_array = np.asarray(a)
    cdef double * cpp_a = &a_array[0]
    self.thisptr.testfun(cpp_a, a_array.shape[0])
""")
