# file endings
cpp_header_endings = ["h", "hh", "hpp"]
python_file_ending = "py"
pyx_file_ending = "pyx"
pxd_file_ending = "pxd"

# operator mapping TODO extend
# http://docs.cython.org/src/reference/special_methods_table.html
operators = {
    "operator()": "__call__",
    "operator[]": "__getitem__",
    "operator+": "__add__",
    "operator-": "__sub__",
    "operator*": "__mul__",
    "operator/": "__div__"
}
call_operators = {
    "operator()": "call",
    "operator[]": "getitem",
    "operator+": "add",
    "operator-": "sub",
    "operator*": "mul",
    "operator/": "div"
}

# declaration templates
typedef_decl = """cdef extern from "%(filename)s" namespace "%(namespace)s":
    ctypedef %(underlying_type)s %(tipe)s"""
enum_decl = """cdef extern from "%(filename)s" namespace "%(namespace)s":
    cdef enum %(tipe)s:
%(constants)s"""
class_decl = """cdef extern from "%(filename)s" namespace "%(namespace)s":
    cdef cppclass %(name)s:"""
function_decl = """cdef extern from "%(filename)s" namespace "%(namespace)s":
    %(result_type)s %(name)s(%(args)s)"""
method_decl = "        %(result_type)s %(name)s(%(args)s)"
constructor_decl = "        %(class_name)s(%(args)s)"
arg_decl = "%(tipe)s %(name)s"
field_decl = "        %(tipe)s %(name)s"

# type definitions
class_def = """cdef class %(name)s:
    cdef cpp.%(name)s * thisptr
    cdef bool delete_thisptr

    def __cinit__(self):
        self.thisptr = NULL
        self.delete_thisptr = True

    def __dealloc__(self):
        if self.delete_thisptr and self.thisptr != NULL:
            del self.thisptr
"""
enum_def = """cdef class %(tipe)s:
%(constants)s
"""

# member definitions
field_def = """    %(name)s = property(get_%(name)s, set_%(name)s)
"""
ctor_default_def = """    def __init__(cpp.%(name)s self):
        self.thisptr = new cpp.%(name)s()
"""

signature_def = "%(def)s %(name)s(%(args)s):"

fun_call = "cpp.%(name)s(%(args)s)"
ctor_call = "self.thisptr = new cpp.%(class_name)s(%(args)s)"
method_call = "self.thisptr.%(name)s(%(args)s)"
setter_call = "self.thisptr.%(name)s = %(call_arg)s"
getter_call = "self.thisptr.%(name)s"

catch_result = "%(cpp_type_decl)s result = %(call)s"

# setup.py

setup_extension = """
    config.add_extension(
        '%(module)s',
        sources=["%(module)s.cpp", "%(filename)s"],
        include_dirs=["%(sourcedir)s", numpy.get_include()],
        define_macros=[("NDEBUG",)],
        extra_compile_args=["-O3"],
        language="c++",
    )
"""

setup_py = """def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration
    import numpy

    config = Configuration('.', parent_package, top_path)
    config.add_extension(
        '%(module)s',
        sources=["%(module)s.cpp", "%(filename)s"],
        include_dirs=["%(sourcedir)s", numpy.get_include()],
        define_macros=[("NDEBUG",)],
        extra_compile_args=["-O3"],
        language="c++")
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
"""

registered_converters = []