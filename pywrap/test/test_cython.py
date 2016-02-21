from pywrap.cython import Includes, Param, FunctionBase
from nose.tools import assert_equal


def test_simple_function_def():
    fun = FunctionBase("testfun")
    assert_equal(
        fun.function_def(Includes("test_module"), result_type="void"),
        """    def testfun(self):
        self.thisptr.testfun()
""")


def test_array_arg_function_def():
    fun = FunctionBase("testfun")
    fun.arguments = [Param("a", "double *"), Param("aSize", "unsigned int")]
    testfun = fun.function_def(Includes("test_module"), result_type="void")
    assert_equal(testfun,
        """    def testfun(self, a):
        cdef np.ndarray[double, ndim=1] a_array = np.asarray(a)
        cdef double * cpp_a = &a_array[0]
        self.thisptr.testfun(cpp_a, a_array.shape[0])
""")