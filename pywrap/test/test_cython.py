from pywrap.cython import Includes, function_def
from nose.tools import assert_equal


def test_simple_function_def():
    assert_equal(
        function_def("testfun", [], Includes("test_module"), result_type="void"),
        """    def testfun(self):
        self.thisptr.testfun()
""")