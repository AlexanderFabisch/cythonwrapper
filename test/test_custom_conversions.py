from pywrap.testing import cython_extension_from
import os
import numpy as np
from numpy.testing import assert_array_equal
from nose.plugins.skip import SkipTest
from pywrap.type_conversion import AbstractTypeConverter
from pywrap.defaultconfig import Config
from pywrap.utils import lines


def test_convert_vector():
    eigen3_incdir = "/usr/include/eigen3"
    if not os.path.exists(eigen3_incdir):
        raise SkipTest("Eigen 3 include directory '%s' not found"
                       % eigen3_incdir)

    eigen_vector_decl = """

cdef extern from "Eigen/Dense" namespace "Eigen":
  cdef cppclass VectorXd:
    VectorXd()
    VectorXd(int rows)
    VectorXd(VectorXd&)
    double* data()
    int rows()
    double& get "operator()"(int rows)

"""

    class EigenConverter(AbstractTypeConverter):
        def __init__(self, tname, python_argname, type_info, context):
            super(EigenConverter, self).__init__(
                tname, python_argname, type_info, context)
            if self.python_argname is not None:
                self.cpp_argname = "cpp_" + python_argname
            else:
                self.cpp_argname = None

        def matches(self):
            return self.tname == "VectorXd"

        def n_cpp_args(self):
            return 1

        def add_includes(self, includes):
            includes.numpy = True
            includes.add_custom_module("eigen_vector")

        def python_to_cpp(self):
            return lines(
                "cdef int %(python_argname)s_length = %(python_argname)s.shape[0]",
                "cdef _eigen_vector.VectorXd %(cpp_argname)s = _eigen_vector.VectorXd(%(python_argname)s_length)",
                "cdef int %(python_argname)s_idx",
                "for %(python_argname)s_idx in range(%(python_argname)s_length):",
                "    %(cpp_argname)s.data()[%(python_argname)s_idx] = %(python_argname)s[%(python_argname)s_idx]"
            ) % {"python_argname": self.python_argname,
                 "cpp_argname": self.cpp_argname}

        def cpp_call_args(self):
            return [self.cpp_argname]

        def return_output(self, copy=True):
            return lines(
                "cdef int size = result.rows()",
                "cdef int res_idx",
                "cdef np.ndarray[double, ndim=1] res = np.ndarray(shape=(size,))",
                "for res_idx in range(size):",
                "    res[res_idx] = result.get(res_idx)",
                "return res"
            )

        def python_type_decl(self):
            return "np.ndarray[double, ndim=1] " + self.python_argname

        def cpp_type_decl(self):
            return "cdef _eigen_vector.VectorXd"

    config = Config()
    config.registered_converters.append(EigenConverter)
    config.add_declaration("eigen_vector", eigen_vector_decl, ["VectorXd"])

    with cython_extension_from("eigen.hpp", config=config,
                               incdirs=eigen3_incdir):
        from eigen import make
        a = np.ones(5)
        assert_array_equal(make(a), a * 2.0)
