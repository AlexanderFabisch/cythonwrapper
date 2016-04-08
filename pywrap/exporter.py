import os
import warnings

from . import defaultconfig as config
from .cpptypeconv import is_type_with_automatic_conversion, \
    cython_define_basic_inputarg, cython_define_nparray1d_inputarg, \
    cython_define_cpp_inputarg
from .utils import indent_block, from_camel_case


class CythonDeclarationExporter:
    """Export AST to Cython declaration file (.pxd).

    This class implements the visitor pattern.
    """
    def __init__(self):
        self.output = ""
        self.ctors = []
        self.methods = []
        self.arguments = []

    def visit_ast(self, ast):
        pass

    def visit_includes(self, includes):
        self.output += includes.header()

    def visit_class(self, clazz):
        class_str = config.class_def % clazz.__dict__

        self.output += (os.linesep + class_str +
                        os.linesep + os.linesep.join(self.ctors) +
                        os.linesep + os.linesep.join(self.methods))

        self.ctors = []
        self.methods = []

    def visit_constructor(self, ctor):
        const_dict = {"args": ", ".join(self.arguments)}
        const_dict.update(ctor.__dict__)
        const_str = config.constructor_def % const_dict
        self.ctors.append(const_str)

        self.arguments = []

    def visit_method(self, method):
        method_dict = {"args": ", ".join(self.arguments)}
        method_dict.update(method.__dict__)
        method_str = config.method_def % method_dict
        self.methods.append(method_str)

        self.arguments = []

    def visit_param(self, param):
        self.arguments.append(config.arg_def % param.__dict__)

    def export(self):
        return self.output


class CythonImplementationExporter:
    """Export AST to Cython implementation file (.pyx).

    This class implements the visitor pattern.
    """
    def __init__(self, classes):
        self.classes = classes
        self.output = ""
        self.ctors = []
        self.methods = []
        self.arguments = []
        self.includes = None

    def visit_ast(self, ast):
        pass

    def visit_includes(self, includes):
        self.includes = includes

    def visit_class(self, clazz):
        if len(self.ctors) > 1:
            msg = ("Class '%s' has more than one constructor. This is not "
                   "compatible to Python. The last constructor will overwrite "
                   "all others." % clazz.name)
            warnings.warn(msg)
        class_str = config.py_class_def % clazz.__dict__
        self.output += (os.linesep + os.linesep + class_str +
                        os.linesep + os.linesep.join(self.ctors) +
                        os.linesep + os.linesep.join(self.methods))

        self.ctors = []
        self.methods = []

    def visit_constructor(self, ctor):
        function_def = ConstructorDefinition(
            ctor.class_name, ctor.name, ctor.arguments, self.includes,
            initial_args=["self"], classes=self.classes).make()
        self.ctors.append(indent_block(function_def, 1))

        self.arguments = []

    def visit_method(self, method):
        function_def = FunctionDefinition(
            method.name, method.arguments, self.includes, ["self"],
            method.result_type, classes=self.classes).make()
        self.methods.append(indent_block(function_def, 1))

        self.arguments = []

    def visit_param(self, param):
        self.arguments.append(config.py_arg_def % param.__dict__)

    def export(self):
        return self.includes.header() + os.linesep + os.linesep + self.output


class FunctionDefinition(object):
    def __init__(self, name, arguments, includes, initial_args, result_type,
                 classes):
        self.name = name
        self.arguments = arguments
        self.includes = includes
        self.initial_args = initial_args
        self.result_type = result_type
        self.classes = classes

    def make(self):
        body, call_args = self._input_type_conversions(self.includes)
        body += self._call_cpp_function(call_args)
        body += self._output_type_conversion()
        return self._signature() + os.linesep + indent_block(body, 1)

    def _call_cpp_function(self, call_args):
        call = "self.thisptr.{fname}({args})".format(
            fname=self.name, args=", ".join(call_args))
        if self.result_type != "void":
            call = "cdef {result_type} result = {call}".format(
                result_type=self.result_type, call=call)
        return call + os.linesep

    def _signature(self):
        args = self._cython_signature_args()
        return "cpdef %s(%s):" % (from_camel_case(self.name), ", ".join(args))

    def _cython_signature_args(self):
        cython_signature_args = []
        cython_signature_args.extend(self.initial_args)
        skip = False
        for arg in self.arguments:
            if skip:
                skip = False
                continue
            if is_type_with_automatic_conversion(arg.tipe):
                tipe = arg.tipe
            elif arg.tipe == "double *":
                skip = True
                tipe = "np.ndarray[double, ndim=1]"
            elif arg.tipe in self.classes:
                tipe = "Cpp" + arg.tipe
            else:
                tipe = ""
            cython_signature_args.append("%s %s" % (tipe, arg.name))
        return cython_signature_args

    def _input_type_conversions(self, includes):
        body = ""
        call_args = []
        skip = False

        for i in range(len(self.arguments)):
            if skip:
                skip = False
                continue

            argument = self.arguments[i]
            cppname = "cpp_" + argument.name

            deref = False
            additional_callarg = None

            if is_type_with_automatic_conversion(argument.tipe):
                body += cython_define_basic_inputarg(
                    argument.tipe, cppname, argument.name) + os.linesep
            elif argument.tipe == "double *":
                includes.numpy = True
                body += cython_define_nparray1d_inputarg(
                    argument.tipe, cppname, argument.name)
                additional_callarg = argument.name + "_array.shape[0]"
                skip = True
            elif argument.tipe.startswith("vector"):
                body += cython_define_basic_inputarg(
                    argument.tipe, cppname, argument.name) + os.linesep
            elif argument.tipe in self.classes:
                # TODO import correct module if it is another one
                body += cython_define_cpp_inputarg(
                    argument.tipe, cppname, argument.name) + os.linesep
                deref = True
            else:
                raise NotImplementedError("No known conversion for type %r"
                                          % argument.tipe)

            if deref:
                includes.add_include_for_deref()
                call_arg = "deref(%s)" % cppname
            else:
                call_arg = cppname

            call_args.append(call_arg)

            if additional_callarg is not None:
                call_args.append(additional_callarg)

        return body, call_args

    def _output_type_conversion(self):
        if self.result_type is None or self.result_type == "void":
            return ""
        elif is_type_with_automatic_conversion(self.result_type):
            return "return result" + os.linesep
        else:
            # TODO only works with default constructor
            cython_classname = "Cpp%s" % self.result_type.split()[0]
            return """ret = %s()
ret.thisptr = result
return ret
""" % cython_classname


class ConstructorDefinition(FunctionDefinition):
    def __init__(self, class_name, name, arguments, includes, initial_args,
                 classes):
        super(ConstructorDefinition, self).__init__(
            name, arguments, includes, initial_args, result_type=None,
            classes=classes)
        self.class_name = class_name

    def _call_cpp_function(self, call_args):
        return "self.thisptr = new %s(%s)%s" % (
            self.class_name, ", ".join(call_args), os.linesep)

    def _signature(self):
        args = self._cython_signature_args()
        return "def __init__(%s):" % ", ".join(args)
