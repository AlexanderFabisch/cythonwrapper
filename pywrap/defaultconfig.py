cpp_header_endings = ["h", "hh", "hpp"]
pyx_file_ending = "pyx"
pxd_file_ending = "pxd"

class_def = """cdef extern from "%(filename)s" namespace "%(namespace)s":
    cdef cppclass %(name)s:"""
method_def = "        %(result_type)s %(name)s(%(args)s)"
constructor_def = "        %(name)s(%(args)s)"
function_def = """cdef extern from "%(filename)s" namespace "%(namespace)s":
    %(result_type)s %(name)s(%(args)s)"""
arg_def = "%(tipe)s %(name)s"
py_class_def = """cdef class Cpp%(name)s:
    cdef %(name)s *thisptr

    def __cinit__(self):
        self.thisptr = NULL

    def __dealloc__(self):
        if self.thisptr != NULL:
            del self.thisptr
"""
py_arg_def = "%(name)s"
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
setup_py = """import os


def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration
    import numpy

    config = Configuration('.', parent_package, top_path)
%(extensions)s
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
"""
