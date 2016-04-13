import os
import warnings
from . import defaultconfig as config
from .type_conversion import (is_type_with_automatic_conversion,
                              create_type_converter)
from .utils import lines, indent_block, from_camel_case


class CythonDeclarationExporter:
    """Export AST to Cython declaration file (.pxd).

    This class implements the visitor pattern.
    """
    def __init__(self):
        self.output = ""
        self.ctors = []
        self.methods = []
        self.arguments = []
        self.fields = []
        self.includes = None

    def visit_ast(self, ast):
        pass

    def visit_includes(self, includes):
        self.includes = includes

    def visit_struct(self, struct):
        struct_decl_parts = [config.struct_def % struct.__dict__,
                             os.linesep.join(self.fields)]
        struct_decl_parts = [p for p in struct_decl_parts if p != ""]
        empty_body = len(self.fields) == 0
        if empty_body:
            struct_decl_parts.append(" " * 8 + "pass")
        self.output += (os.linesep * 2 + os.linesep.join(struct_decl_parts) +
                        os.linesep * 2)
    def visit_field(self, field):
        self.fields.append(config.field_def % field.__dict__)

    def visit_class(self, clazz):
        class_decl_parts = [config.class_def % clazz.__dict__,
                            os.linesep.join(self.ctors),
                            os.linesep.join(self.methods)]
        class_decl_parts = [p for p in class_decl_parts if p != ""]
        empty_body = len(self.methods) == 0 and len(self.ctors) == 0
        if empty_body:
            class_decl_parts.append(" " * 8 + "pass")
        self.output += (os.linesep * 2 + os.linesep.join(class_decl_parts) +
                        os.linesep * 2)

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
        method_dict["name"] = map_method_decl(method_dict["name"])
        method_str = config.method_def % method_dict
        self.methods.append(method_str)
        self.arguments = []

    def visit_function(self, function):
        function_dict = {"args": ", ".join(self.arguments)}
        function_dict.update(function.__dict__)
        function_str = config.function_def % function_dict
        self.output += (os.linesep * 2 + function_str + os.linesep)
        self.arguments = []

    def visit_param(self, param):
        self.arguments.append(config.arg_def % param.__dict__)

    def export(self):
        return self.includes.declarations_import() + self.output


def map_method_decl(method_name):
    if method_name in config.call_operators:
        return "%s \"%s\"" % (config.call_operators[method_name], method_name)
    else:
        return method_name


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
        self.fields = []
        self.includes = None

    def visit_ast(self, ast):
        pass

    def visit_includes(self, includes):
        self.includes = includes

    def visit_struct(self, struct):
        struct_def_parts = [config.py_struct_def % struct.__dict__,
                            os.linesep.join(self.fields)]
        struct_def_parts = [p for p in struct_def_parts if p != ""]
        self.output += (os.linesep * 2 + os.linesep.join(struct_def_parts) +
                        os.linesep * 2)

    def visit_field(self, field):
        field_def = config.py_field_def % {"name": field.name} + os.linesep
        self.fields.append(field_def)

    def visit_class(self, clazz):
        if len(self.ctors) > 1:
            msg = ("Class '%s' has more than one constructor. This is not "
                   "compatible to Python. The last constructor will overwrite "
                   "all others." % clazz.name)
            warnings.warn(msg)

        class_def_parts = [config.py_class_def % clazz.__dict__,
                           os.linesep.join(self.ctors),
                           os.linesep.join(self.methods)]
        class_def_parts = [p for p in class_def_parts if p != ""]
        self.output += (os.linesep * 2 + os.linesep.join(class_def_parts) +
                        os.linesep * 2)

        self.ctors = []
        self.methods = []

    def visit_constructor(self, ctor):
        try:
            function_def = ConstructorDefinition(
                ctor.class_name, ctor.name, ctor.arguments, self.includes,
                initial_args=[ctor.class_name + " self"],
                classes=self.classes).make()
            self.ctors.append(indent_block(function_def, 1))
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring method '%s'" % ctor.name)
        finally:
            self.arguments = []

    def visit_method(self, method):
        try:
            method_def = MethodDefinition(
                method.name, method.arguments, self.includes,
                [method.class_name + " self"], method.result_type,
                classes=self.classes).make()
            self.methods.append(indent_block(method_def, 1))
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring method '%s'" % method.name)
        finally:
            self.arguments = []

    def visit_function(self, function):
        try:
            function_def = FunctionDefinition(
                function.name, function.arguments, self.includes, [],
                function.result_type, classes=self.classes).make()
            self.output += (os.linesep * 2 + function_def + os.linesep)
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring function '%s'" % function.name)
        finally:
            self.arguments = []

    def visit_param(self, param):
        self.arguments.append(config.py_arg_def % param.__dict__)

    def export(self):
        return self.includes.implementations_import() + self.output


class FunctionDefinition(object):
    def __init__(self, name, arguments, includes, initial_args, result_type,
                 classes):
        self.name = name
        self.arguments = arguments
        self.includes = includes
        self.initial_args = initial_args
        self.result_type = result_type
        self.classes = classes
        self.type_converters = []

    def make(self):
        self._create_type_converters()
        body, call_args = self._input_type_conversions(self.includes)
        body += self._call_cpp_function(call_args)
        body += self.output_type_converter.return_output()
        return self._signature() + os.linesep + indent_block(body, 1)

    def _create_type_converters(self):
        skip = 0
        for arg in self.arguments:
            if skip > 0:
                skip -= 1
                continue
            type_converter = create_type_converter(
                arg.tipe, arg.name, self.classes)
            type_converter.add_includes(self.includes)
            self.type_converters.append(type_converter)
            skip = type_converter.n_cpp_args() - 1
        self.output_type_converter = create_type_converter(
            self.result_type, None, self.classes)
        self.output_type_converter.add_includes(self.includes)

    def _call_cpp_function(self, call_args):
        call = "cpp.{fname}({args})".format(
            fname=self.name, args=", ".join(call_args))
        if self.result_type != "void":
            call = "cdef {result_type} result = {call}".format(
                result_type=self.result_type, call=call)
        return call + os.linesep

    def _signature(self):
        args = self._cython_signature_args()
        return "def %s(%s):" % (from_camel_case(self.name), ", ".join(args))

    def _cython_signature_args(self):
        cython_signature_args = []
        cython_signature_args.extend(self.initial_args)
        for type_converter in self.type_converters:
            arg = type_converter.python_type_decl()
            cython_signature_args.append(arg)
        return cython_signature_args

    def _input_type_conversions(self, includes):
        body = ""
        call_args = []
        for type_converter in self.type_converters:
            body += type_converter.python_to_cpp() + os.linesep
            call_args.extend(type_converter.cpp_call_args())
        return body, call_args


class ConstructorDefinition(FunctionDefinition):
    def __init__(self, class_name, name, arguments, includes, initial_args,
                 classes):
        super(ConstructorDefinition, self).__init__(
            name, arguments, includes, initial_args, result_type=None,
            classes=classes)
        self.class_name = class_name

    def _call_cpp_function(self, call_args):
        return "self.thisptr = new cpp.%s(%s)%s" % (
            self.class_name, ", ".join(call_args), os.linesep)

    def _signature(self):
        args = self._cython_signature_args()
        return "def __init__(%s):" % ", ".join(args)


class MethodDefinition(FunctionDefinition):
    def _call_cpp_function(self, call_args):
        call = "self.thisptr.{fname}({args})".format(
            fname=self._python_call_method(), args=", ".join(call_args))
        if self.result_type != "void":
            call = "cdef {result_type} result = {call}".format(
                result_type=self.output_type_converter.cpp_type_decl(),
                call=call)
        return call + os.linesep

    def _signature(self):
        args = self._cython_signature_args()
        method_name = self._python_method_name()
        def_prefix = self._def_prefix(method_name)
        return "%s %s(%s):" % (def_prefix, method_name, ", ".join(args))

    def _def_prefix(self, method_name):
        special_method = (method_name.startswith("__") and
                          method_name.endswith("__"))
        if special_method:
            return "def"
        else:
            return "cpdef"

    def _python_call_method(self):
        if self.name in config.call_operators:
            return config.call_operators[self.name]
        else:
            return self.name

    def _python_method_name(self):
        if self.name in config.operators:
            return config.operators[self.name]
        else:
            return from_camel_case(self.name)
