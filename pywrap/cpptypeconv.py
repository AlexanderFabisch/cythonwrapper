def is_basic_type(typename):
    # TODO This is not a complete list of the fundamental types. The reason is
    # that I don't know if they all will be converted correctly between Python
    # and C++ by Cython. See http://en.cppreference.com/w/cpp/language/types
    # for a complete list.
    return typename in ["int", "unsigned int", "long", "unsigned long",
                        "float", "double"]


def is_type_with_automatic_conversion(typename):
    return is_basic_type(typename) or typename in ["bool", "string"]


def typename(tname):
    """Get cython type from C++ type."""
    # TODO does not work with std::vector<namespace::type>
    cython_tname = tname
    cython_tname = _remove_const_modifier(cython_tname)
    cython_tname = _remove_reference_modifier(cython_tname)
    cython_tname = _remove_namespace(cython_tname)
    cython_tname = _replace_angle_brackets(cython_tname)
    return cython_tname


def _remove_const_modifier(tname):
    return tname.replace("const ", "")


def _remove_reference_modifier(tname):
    return tname.replace(" &", "")


def _remove_namespace(tname):
    return tname.split("::")[-1]


def _replace_angle_brackets(tname):
    return tname.replace("<", "[").replace(">", "]")


def cython_define_basic_inputarg(cython_tname, cython_argname, python_argname):
    return "%scdef %s %s = %s" % (_intend(2), cython_tname, cython_argname,
                                  python_argname)


def cython_define_nparray1d_inputarg(cython_tname, cython_argname, python_argname):
    return (
"""%scdef np.ndarray[double, ndim=1] %s_array = np.asarray(%s)
%scdef %s %s = &%s_array[0]
"""
             % (_intend(2), python_argname, python_argname,
                _intend(2), cython_tname, cython_argname, python_argname))


def _intend(level):
    return "    " * level
