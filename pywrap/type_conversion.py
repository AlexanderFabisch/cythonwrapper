import os
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
    return is_basic_type(typename) or typename in ["bool", "string", "char *"]


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


def _is_pointer(tname):
    parts = tname.split()
    return len(parts) == 2 and parts[1] == "*"


def _type_without_pointer(tname):
    return tname.split()[0]


def underlying_type(tname, typedefs):
    while tname in typedefs:
        tname = typedefs[tname]
    return tname


def typedef_prefix(tname, typedefs):
    if tname in typedefs:
        return "cpp." + tname
    else:
        return tname


def create_type_converter(tname, python_argname, classes, typedefs,
                          context=None):
    converters = []
    converters.extend(registered_converters)
    converters.extend(default_converters)
    for Converter in converters:
        converter = Converter(tname, python_argname, classes, typedefs, context)
        if converter.matches():
            return converter
    raise NotImplementedError(
        "No type converter available for type '%s', using the Python object "
        "converter." % tname)


class AbstractTypeConverter(object):
    __metaclass__ = ABCMeta

    def __init__(self, tname, python_argname, classes, typedefs, context=None):
        self.tname = tname
        self.python_argname = python_argname
        self.classes = classes
        self.typedefs = typedefs
        self.context = context

    @abstractmethod
    def matches(self):
        """Is the type converter applicable to the type?"""

    @abstractmethod
    def n_cpp_args(self):
        """Number of C++ arguments that are covered by this converter."""

    def add_includes(self, includes):
        """Add includes for this conversion."""

    @abstractmethod
    def python_to_cpp(self):
        """Convert Cython object to C++ object."""

    @abstractmethod
    def cpp_call_args(self):
        """Representation for C++ function call."""

    def return_output(self):
        """Return output of a C++ function in Cython."""
        return "return result" + os.linesep

    @abstractmethod
    def cpp_type_decl(self):
        """Representation for C++ type declaration."""

    @abstractmethod
    def cpp_type_decl(self):
        """C++ type declaration."""


class VoidTypeConverter(AbstractTypeConverter):
    def matches(self):
        return (self.tname is None or
                underlying_type(self.tname, self.typedefs) == "void")

    def n_cpp_args(self):
        raise NotImplementedError()

    def python_to_cpp(self):
        raise NotImplementedError()

    def cpp_call_args(self):
        raise NotImplementedError()

    def return_output(self):
        return ""

    def cpp_type_decl(self):
        return typedef_prefix(self.tname, self.typedefs)

    def python_type_decl(self):
        raise NotImplementedError()


class AutomaticTypeConverter(AbstractTypeConverter):
    def matches(self):
        return is_type_with_automatic_conversion(
            underlying_type(self.tname, self.typedefs))

    def n_cpp_args(self):
        return 1

    def cpp_call_args(self):
        return ["cpp_" + self.python_argname]

    def python_to_cpp(self):
        cython_argname = "cpp_" + self.python_argname
        return cython_define_basic_inputarg(
            typedef_prefix(self.tname, self.typedefs), cython_argname,
            self.python_argname)

    def python_type_decl(self):
        return "%s %s" % (typedef_prefix(self.tname, self.typedefs),
                          self.python_argname)

    def cpp_type_decl(self):
        return typedef_prefix(self.tname, self.typedefs)


class DoubleArrayTypeConverter(AbstractTypeConverter):
    def matches(self):
        if self.context is None:
            return False
        args, index = self.context
        next_arg_is_int = len(args) >= index + 2 and args[index + 1]
        return self.tname == "double *" and next_arg_is_int

    def n_cpp_args(self):
        return 2

    def add_includes(self, includes):
        includes.numpy = True

    def python_to_cpp(self):
        return ""

    def cpp_call_args(self):
        return ["&%s[0]" % self.python_argname,
                self.python_argname + ".shape[0]"]

    def return_output(self):
        raise NotImplementedError()

    def python_type_decl(self):
        return "np.ndarray[double, ndim=1] %s" % self.python_argname

    def cpp_type_decl(self):
        return "double *"


class CythonTypeConverter(AbstractTypeConverter):
    def matches(self):
        return underlying_type(self.tname, self.typedefs) in self.classes

    def n_cpp_args(self):
        return 1

    def add_includes(self, includes):
        includes.add_include_for_deref()

    def python_to_cpp(self):
        cython_argname = "cpp_" + self.python_argname
        return ("cdef %s * %s = %s.thisptr"
                % (self.cpp_type_decl(), cython_argname, self.python_argname))

    def cpp_call_args(self):
        return ["deref(cpp_%s)" % self.python_argname]

    def return_output(self):
        raise NotImplementedError()

    def python_type_decl(self):
        return "%s %s" % (typedef_prefix(self.tname, self.typedefs),
                          self.python_argname)

    def cpp_type_decl(self):
        return "cpp.%s" % self.tname


class CppPointerTypeConverter(AbstractTypeConverter):
    def __init__(self, tname, python_argname, classes, typedefs, context=None):
        super(CppPointerTypeConverter, self).__init__(
            tname, python_argname, classes, typedefs, context)
        self.tname_wo_ptr = _type_without_pointer(tname)

    def matches(self):
        if _is_pointer(self.tname):
            return underlying_type(_type_without_pointer(self.tname),
                                   self.typedefs) in self.classes
        else:
            tname = underlying_type(self.tname, self.typedefs)
            return (_is_pointer(tname) and
                    _type_without_pointer(self.tname) in self.classes)

    def n_cpp_args(self):
        return 1

    def python_to_cpp(self):
        cython_argname = "cpp_" + self.python_argname
        return ("cdef %s %s = %s.thisptr"
                % (self.cpp_type_decl(), cython_argname, self.python_argname))

    def cpp_call_args(self):
        return ["cpp_%s" % self.python_argname]

    def return_output(self):
        # TODO only works with default constructor
        return lines("ret = %s()" % self.tname_wo_ptr,
                     "ret.thisptr = result",
                     "return ret")

    def python_type_decl(self):
        return "%s %s" % (typedef_prefix(self.tname_wo_ptr, self.typedefs),
                          self.python_argname)

    def cpp_type_decl(self):
        return "cpp.%s" % self.tname


class PythonObjectConverter(AbstractTypeConverter):
    def matches(self):
        return True

    def n_cpp_args(self):
        return 1

    def python_to_cpp(self):
        raise NotImplementedError(
            "No known conversion from python type to '%s' (name: '%s')"
            % (self.tname, self.python_argname))

    def cpp_call_args(self):
        return ["cpp_" + self.python_argname]

    def python_type_decl(self):
        return "object %s" % self.python_argname

    def cpp_type_decl(self):
        return typedef_prefix(self.tname, self.typedefs)


class StlTypeConverter(PythonObjectConverter):
    def matches(self):
        tname = underlying_type(self.tname, self.typedefs)
        return tname.startswith("vector") or tname.startswith("map")

    def cpp_call_args(self):
        return ["cpp_" + self.python_argname]

    def python_to_cpp(self):
        cython_argname = "cpp_" + self.python_argname
        return cython_define_basic_inputarg(
            typedef_prefix(self.tname, self.typedefs), cython_argname,
            self.python_argname)


default_converters = [
    AutomaticTypeConverter, VoidTypeConverter, DoubleArrayTypeConverter,
    CythonTypeConverter, CppPointerTypeConverter, StlTypeConverter,
    PythonObjectConverter]

registered_converters = []