import os
import re
from abc import ABCMeta, abstractmethod
from .utils import lines
from .templates import render


def is_basic_type_with_automatic_conversion(typename):
    # source: http://docs.cython.org/src/userguide/wrapping_CPlusPlus.html#standard-library
    return typename in ["bool", "string", "char *",
                        "int", "unsigned int", "long", "unsigned long",
                        "float", "double"]


def is_stl_type_with_automatic_conversion(typename):
    # source: http://docs.cython.org/src/userguide/wrapping_CPlusPlus.html#standard-library
    for container in ["string", "map", "vector", "list", "set", "pair"]:
        if typename.startswith(container):
            return True
    return False


def cythontype_from_cpptype(tname):
    """Get Cython type from C++ type."""
    cython_tname = tname
    cython_tname = _remove_const_modifier(cython_tname)
    cython_tname = _remove_reference_modifier(cython_tname)
    cython_tname = _remove_namespace(cython_tname)
    cython_tname = _replace_angle_brackets(cython_tname)
    return cython_tname


def _remove_const_modifier(tname):
    return tname.replace("const ", "").replace("*const", "*").strip()


def _remove_reference_modifier(tname):
    return tname.replace(" &", "")


def _remove_namespace(tname):
    result = tname
    while "::" in result:
        parts = result.split("::")
        head = parts[0]
        tail = "::".join(parts[1:])
        if tail in ["iterator", "const_iterator"]:
            raise NotImplementedError("Cannot handle iterator types")

        last_sep = head.rfind(", ")
        last_open = head.rfind("<")
        if last_sep >= 0 and last_sep > last_open:
            head = head[:last_sep + 2]
        else:
            head = head[:last_open + 1]

        result = head + tail
    return result


def _replace_angle_brackets(tname):
    return tname.replace("<", "[").replace(">", "]")


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


def find_all_subtypes(tname):
    tname = tname.replace(" ", "")
    result = set()
    while len(tname) > 1:
        match = re.match("([,\[\]]?([a-zA-Z0-9_\*]+?)[,\[\]]).*", tname)
        if match is None:
            return result

        subtname = match.group(2)
        subtname = subtname.replace("*", " *")
        result.add(subtname)
        tname = tname[len(match.group(1)) - 1:]
    return list(result)


def create_type_converter(tname, python_argname, type_info, config,
                          context=None):
    converters = []
    converters.extend(config.registered_converters)
    converters.extend(default_converters)
    for Converter in converters:
        converter = Converter(tname, python_argname, type_info, context)
        if converter.matches():
            return converter
    raise NotImplementedError(
        "No type converter available for type '%s', using the Python object "
        "converter." % tname)


class AbstractTypeConverter(object):
    """Type converter interface.

    A type converter defines everything that is required to handle conversions
    from a C++ type to a Python type. It will be used to define Cython
    functions that wrap C++ code. These are constructors, methods, getters,
    setters and free functions. You can define your own type converter
    and add it to the list 'registered_converters' this module.

    Here is an example with a method definition:

    .. code-block:: python

        from libcpp.vector cimport vector

        ...

            cpdef my_function(cpp.MyType self, object a, double b):
                cdef vector[double] cpp_a = a
                cdef double cpp_b = b
                cdef int result = self.thisptr.myFunction(cpp_a, cpp_b)
                return result

    Parts
    -----
    add_includes     - add required includes for the converter, in this example
                       we need to import vector for the parameter 'a'
    matches          - for a given C++ argument, the function tells if the
                       converter can be used
    n_cpp_args       - number of C++ arguments that are covered by the Python
                       object, is 1 for each parameter of the function, e.g.
                       'a' and 'b'
    python_to_cpp    - conversion from Python type to C++ type, e.g.
                       'cdef vector[double] cpp_a = a'
    cpp_call_args    - name of the arguments that will be used to call the
                       C++ function, e.g. 'cpp_a' and 'cpp_b'
    return_output    - converts and returns output, simply 'return result' if
                       no conversion is required
    cpp_type_decl    - decleration of C++ type to declare the type of the output
                       of the C++ function call, e.g. 'cdef int'
    python_type_decl - decleration of the Python type to declare the types
                       in the signature of the Python function
    """
    __metaclass__ = ABCMeta

    def __init__(self, tname, python_argname, type_info, context=None):
        self.tname = tname
        self.python_argname = python_argname
        self.type_info = type_info
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

    def return_output(self, copy=True):
        """Return output of a C++ function in Cython."""
        return "return result" + os.linesep

    @abstractmethod
    def python_type_decl(self):
        """Python type decleration."""

    @abstractmethod
    def cpp_type_decl(self):
        """C++ type declaration."""


class VoidTypeConverter(AbstractTypeConverter):
    def matches(self):
        return (self.tname is None or
                underlying_type(self.tname, self.type_info.typedefs) == "void")

    def n_cpp_args(self):
        raise NotImplementedError()

    def python_to_cpp(self):
        raise NotImplementedError()

    def cpp_call_args(self):
        raise NotImplementedError()

    def return_output(self, copy=True):
        return ""

    def python_type_decl(self):
        raise NotImplementedError()

    def cpp_type_decl(self):
        return ""


class AutomaticTypeConverter(AbstractTypeConverter):
    def matches(self):
        return is_basic_type_with_automatic_conversion(
            underlying_type(self.tname, self.type_info.typedefs))

    def n_cpp_args(self):
        return 1

    def cpp_call_args(self):
        return ["cpp_" + self.python_argname]

    def python_to_cpp(self):
        cython_argname = "cpp_" + self.python_argname
        return "%s %s = %s" % (self.cpp_type_decl(), cython_argname,
                               self.python_argname)

    def python_type_decl(self):
        return "%s %s" % (typedef_prefix(self.tname, self.type_info.typedefs),
                          self.python_argname)

    def cpp_type_decl(self):
        return "cdef " + typedef_prefix(self.tname, self.type_info.typedefs)


class AutomaticPointerTypeConverter(AbstractTypeConverter):
    def matches(self):
        return (_is_pointer(self.tname) and
                is_basic_type_with_automatic_conversion(underlying_type(
                    _type_without_pointer(self.tname),
                    self.type_info.typedefs)))

    def n_cpp_args(self):
        return 1

    def cpp_call_args(self):
        return ["cpp_" + self.python_argname]

    def python_to_cpp(self):
        cython_argname = "cpp_" + self.python_argname
        return "%s %s = &%s" % (self.cpp_type_decl(), cython_argname,
                                self.python_argname)

    def python_type_decl(self):
        python_tname = _type_without_pointer(typedef_prefix(
            _type_without_pointer(self.tname), self.type_info.typedefs))
        return "%s %s" % (python_tname, self.python_argname)

    def cpp_type_decl(self):
        return "cdef " + self.tname

    def return_output(self, copy=True):
        raise NotImplementedError()


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

    def return_output(self, copy=True):
        raise NotImplementedError()

    def python_type_decl(self):
        return "np.ndarray[double, ndim=1] %s" % self.python_argname

    def cpp_type_decl(self):
        return "cdef double *"


class CStringTypeConverter(AbstractTypeConverter):
    def matches(self):
        return self.tname == "char *"

    def n_cpp_args(self):
        return 1

    def python_to_cpp(self):
        return ""

    def cpp_call_args(self):
        return [self.python_argname]

    def python_type_decl(self):
        return self.tname + " " + self.python_argname

    def cpp_type_decl(self):
        return "cdef const char *"


class EnumConverter(AbstractTypeConverter):
    def matches(self):
        return (underlying_type(self.tname, self.type_info.typedefs) in
                self.type_info.enums)

    def n_cpp_args(self):
        return 1

    def add_includes(self, includes):
        pass

    def python_to_cpp(self):
        return ""

    def cpp_call_args(self):
        return [self.python_argname]

    def return_output(self, copy=True):
        raise NotImplementedError("Cannot return enum")

    def python_type_decl(self):
        return "cpp.%s %s" % (self.tname, self.python_argname)

    def cpp_type_decl(self):
        return "cdef " + self.tname


class CythonTypeConverter(AbstractTypeConverter):
    def matches(self):
        return (underlying_type(self.tname, self.type_info.typedefs) in
                self.type_info.classes)

    def n_cpp_args(self):
        return 1

    def add_includes(self, includes):
        includes.add_include_for_deref()

    def python_to_cpp(self):
        cython_argname = "cpp_" + self.python_argname
        return ("%s * %s = %s.thisptr"
                % (self.cpp_type_decl(), cython_argname, self.python_argname))

    def cpp_call_args(self):
        return ["deref(cpp_%s)" % self.python_argname]

    def return_output(self, copy=True):
        # TODO only works with copy constructor
        return lines("ret = %s()" % self.tname,
                     "ret.thisptr[0] = result",
                     "return ret")

    def python_type_decl(self):
        return "%s %s" % (typedef_prefix(self.tname, self.type_info.typedefs),
                          self.python_argname)

    def cpp_type_decl(self):
        return "cdef cpp.%s" % self.tname


class CppPointerTypeConverter(AbstractTypeConverter):
    def __init__(self, tname, python_argname, type_info, context=None):
        super(CppPointerTypeConverter, self).__init__(
            tname, python_argname, type_info, context)
        self.tname_wo_ptr = _type_without_pointer(tname)

    def matches(self):
        if _is_pointer(self.tname):
            return (underlying_type(_type_without_pointer(self.tname),
                                    self.type_info.typedefs) in
                    self.type_info.classes)
        else:
            tname = underlying_type(self.tname, self.type_info.typedefs)
            return (_is_pointer(tname) and
                    _type_without_pointer(self.tname) in self.type_info.classes)

    def n_cpp_args(self):
        return 1

    def python_to_cpp(self):
        cython_argname = "cpp_" + self.python_argname
        return ("%s %s = %s.thisptr"
                % (self.cpp_type_decl(), cython_argname, self.python_argname))

    def cpp_call_args(self):
        return ["cpp_%s" % self.python_argname]

    def return_output(self, copy=True):
        # TODO only works with default constructor
        l = ["ret = %s()" % self.tname_wo_ptr,
             "ret.thisptr = result"]
        if not copy:
            l.append("ret.delete_thisptr = False")
        l.append("return ret")
        return lines(*l)

    def python_type_decl(self):
        return "%s %s" % (typedef_prefix(self.tname_wo_ptr,
                                         self.type_info.typedefs),
                          self.python_argname)

    def cpp_type_decl(self):
        return "cdef cpp.%s" % self.tname


class StlTypeConverter(AbstractTypeConverter):
    def matches(self):
        tname = underlying_type(self.tname, self.type_info.typedefs)
        return is_stl_type_with_automatic_conversion(tname)

    def n_cpp_args(self):
        return 1

    def add_includes(self, includes):
        includes.add_include_for_deref()

    def cpp_call_args(self):
        return ["cpp_" + self.python_argname]

    def python_type_decl(self):
        return "object %s" % self.python_argname

    def python_to_cpp(self):
        # TODO does not work for complex template type hierarchies
        subtypes = find_all_subtypes(self.tname)
        subtypes = [underlying_type(s, self.type_info.typedefs)
                    for s in subtypes]
        cython_argname = "cpp_" + self.python_argname

        if (self.tname.startswith("vector") and
                    subtypes[1] in self.type_info.classes):
            conversion = render(
                "convert_vector", python_argname=self.python_argname,
                cpp_tname=underlying_type(subtypes[1], self.type_info.typedefs),
                cpp_type_decl=self.cpp_type_decl(),
                cython_argname=cython_argname)
        else:
            conversion = "%s %s = %s" % (self.cpp_type_decl(), cython_argname,
                                         self.python_argname)
        return conversion

    def cpp_type_decl(self):
        tname = self.tname
        subtypes = find_all_subtypes(tname)
        for subtype in subtypes:
            prefixed_subtype = typedef_prefix(subtype, self.type_info.typedefs)
            if (prefixed_subtype in self.type_info.enums or
                        prefixed_subtype in self.type_info.classes):
                prefixed_subtype = "cpp." + prefixed_subtype
            tname = tname.replace(subtype, prefixed_subtype)
        return "cdef " + tname


default_converters = [
    DoubleArrayTypeConverter, CStringTypeConverter, VoidTypeConverter,
    AutomaticTypeConverter, AutomaticPointerTypeConverter, EnumConverter,
    CythonTypeConverter, CppPointerTypeConverter, StlTypeConverter]
