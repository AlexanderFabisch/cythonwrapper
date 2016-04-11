from _declarations cimport *


cdef extern from "test/struct.hpp" namespace "":
    cdef struct A:
        int a

