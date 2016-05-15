from pywrap.type_conversion import AbstractTypeConverter
from pywrap.defaultconfig import Config
from pywrap.utils import lines


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

    def python_to_cpp(self):
        return lines(
            "cdef int %(python_argname)s_length = %(python_argname)s.shape[0]",
            "cdef cpp.VectorXd %(cpp_argname)s = cpp.VectorXd(%(python_argname)s_length)",
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
        return "cdef cpp.VectorXd"


config = Config()
config.registered_converters.append(EigenConverter)
config.add_decleration(eigen_vector_decl)
