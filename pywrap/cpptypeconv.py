import warnings
from abc import ABCMeta, abstractmethod
from .utils import lines


def is_basic_type(typename):
    # TODO This is not a complete list of the fundamental types. The reason is
    # that I don't know if they all will be converted correctly between Python
    # and C++ by Cython. See http://en.cppreference.com/w/cpp/language/types
    # for a complete list.
    return typename in ["int", "unsigned int", "long", "unsigned long",
                        "float", "double"]


def is_type_with_automatic_conversion(typename):
    # TODO add more types from this list:
    # http://docs.cython.org/src/userguide/wrapping_CPlusPlus.html#standard-library
    return is_basic_type(typename) or typename in ["bool", "string"]


def typename(tname):
    """Get cython type from C++ type."""
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
    indices = _find_template_arg_indices(tname)
    new_tname = tname
    shrinked_amount = 0
    for start, end in reversed(indices):
        tname_with_namespace = new_tname[start:end - shrinked_amount]
        if "::" not in tname_with_namespace:
            continue
        tname_without_namespace = "::".join(
            tname_with_namespace.split("::")[1:])
        shrinked_amount += len(tname_without_namespace) - (end - start)
        new_tname = new_tname.replace(new_tname[start:end],
                                      tname_without_namespace)
    return new_tname


def _find_template_arg_indices(tname, indices=None, idx=0):
    # TODO does not work with std::map<std::string, std::string>
    if indices is None:
        indices = [(0, len(tname))]

    start = tname[idx:].find("<")
    if start < 0:
        return indices
    else:
        start += idx + 1

    indices = _find_template_arg_indices(tname, indices, idx=start)
    if len(tname) > indices[-1][1] > start:
        end = indices[-1][1] + tname[indices[-1][1]:].find(">")
    else:
        end = start + tname[start:].find(">")
    indices.append((start, end))

    return indices


def _replace_angle_brackets(tname):
    return tname.replace("<", "[").replace(">", "]")


def cython_define_basic_inputarg(cython_tname, cython_argname, python_argname):
    return "cdef %s %s = %s" % (cython_tname, cython_argname, python_argname)


def create_type_converter(tname, python_argname, classes):
    # TODO extend with plugin mechanism
    if is_type_with_automatic_conversion(tname):
        return AutomaticTypeConverter(tname, python_argname)
    elif tname == "double *":
        return DoubleArrayTypeConverter(python_argname)
    elif tname.startswith("vector"):
        return VectorTypeConverter(tname, python_argname)
    elif tname in classes:
        return CythonTypeConverter(tname, python_argname)
    else:
        warnings.warn("No type converter available for type '%s', using the "
                      "Python object converter." % tname)
        return PythonObjectConverter(python_argname)


class AbstractTypeConverter(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def cython_signature(self):
        """Representation for Cython signature."""

    @abstractmethod
    def n_cpp_args(self):
        """Number of C++ arguments that are covered by this converter."""

    @abstractmethod
    def add_includes(self, includes):
        """Add includes for this conversion."""

    @abstractmethod
    def python_to_cpp(self):
        """Convert Cython object to C++ object."""

    @abstractmethod
    def cpp_call_args(self):
        """Representation for C++ function call."""


class AutomaticTypeConverter(AbstractTypeConverter):
    def __init__(self, tname, python_argname):
        self.tname = tname
        self.python_argname = python_argname

    def cython_signature(self):
        return "%s %s" % (self.tname, self.python_argname)

    def n_cpp_args(self):
        return 1

    def add_includes(self, includes):
        pass

    def python_to_cpp(self):
        cython_argname = "cpp_" + self.python_argname
        return cython_define_basic_inputarg(
            self.tname, cython_argname, self.python_argname)

    def cpp_call_args(self):
        return ["cpp_" + self.python_argname]


class DoubleArrayTypeConverter(AbstractTypeConverter):
    def __init__(self, python_argname):
        self.python_argname = python_argname

    def cython_signature(self):
        return "np.ndarray[double, ndim=1] %s" % self.python_argname

    def n_cpp_args(self):
        return 2

    def add_includes(self, includes):
        includes.numpy = True

    def python_to_cpp(self):
        return (lines(
            "cdef np.ndarray[double, ndim=1] {python_argname}_array = "
            "np.asarray({python_argname})",
            "cdef {cython_tname} {cython_argname} = "
            "&{python_argname}_array[0]").format(
            cython_tname="double *",
            cython_argname="cpp_" + self.python_argname,
            python_argname=self.python_argname))

    def cpp_call_args(self):
        return ["cpp_" + self.python_argname,
                self.python_argname + "_array.shape[0]"]


class CythonTypeConverter(AbstractTypeConverter):
    def __init__(self, tname, python_argname):
        self.tname = tname
        self.python_argname = python_argname

    def cython_signature(self):
        return "Cpp%s %s" % (self.tname, self.python_argname)

    def n_cpp_args(self):
        return 1

    def add_includes(self, includes):
        includes.add_include_for_deref()
        # TODO import correct module if it is another one

    def python_to_cpp(self):
        cython_argname = "cpp_" + self.python_argname
        return ("cdef %s* %s = %s.thisptr"
                % (self.tname, cython_argname, self.python_argname))

    def cpp_call_args(self):
        return ["deref(cpp_%s)" % self.python_argname]


class PythonObjectConverter(AbstractTypeConverter):
    def __init__(self, python_argname):
        self.python_argname = python_argname

    def cython_signature(self):
        return "object %s" % self.python_argname

    def n_cpp_args(self):
        return 1

    def add_includes(self, includes):
        pass

    def python_to_cpp(self):
        raise NotImplementedError()

    def cpp_call_args(self):
        return ["cpp_" + self.python_argname]


class VectorTypeConverter(PythonObjectConverter):
    def __init__(self, tname, python_argname):
        super(VectorTypeConverter, self).__init__(python_argname)
        self.tname = tname

    def python_to_cpp(self):
        cython_argname = "cpp_" + self.python_argname
        return cython_define_basic_inputarg(
            self.tname, cython_argname, self.python_argname)

    def cpp_call_args(self):
        return ["cpp_" + self.python_argname]
