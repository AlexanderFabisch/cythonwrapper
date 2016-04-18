import os
import warnings

from . import defaultconfig as config
from .type_conversion import create_type_converter
from .utils import indent_block, from_camel_case


class CythonDeclarationExporter:
    """Export AST to Cython declaration file (.pxd).

    This class implements the visitor pattern.
    """
    def __init__(self, includes):
        self.includes = includes
        self.output = ""
        self.ctors = []
        self.methods = []
        self.arguments = []
        self.fields = []

    def visit_ast(self, ast):
        pass

    def visit_enum(self, enum):
        enum_decl_dict = {}
        enum_decl_dict.update(enum.__dict__)
        enum_decl_dict["constants"] = indent_block(
            os.linesep.join(enum.constants), 2)
        self.output += config.enum_decl % enum_decl_dict + os.linesep

    def visit_typedef(self, typedef):
        self.output += config.typedef_decl % typedef.__dict__ + os.linesep

    def visit_field(self, field):
        self.fields.append(config.field_decl % field.__dict__)

    def visit_class(self, clazz):
        class_decl_parts = [config.class_decl % clazz.__dict__,
                            os.linesep.join(self.fields),
                            os.linesep.join(self.ctors),
                            os.linesep.join(self.methods)]
        class_decl_parts = [p for p in class_decl_parts if p != ""]
        empty_body = len(self.fields) + len(self.methods) + len(self.ctors) == 0
        if empty_body:
            class_decl_parts.append(" " * 8 + "pass")
        self.output += os.linesep * 2 + os.linesep.join(class_decl_parts)

        self.fields = []
        self.ctors = []
        self.methods = []

    def visit_constructor(self, ctor):
        const_dict = {"args": ", ".join(self.arguments)}
        const_dict.update(ctor.__dict__)
        const_str = config.constructor_decl % const_dict
        self.ctors.append(const_str)
        self.arguments = []

    def visit_method(self, method):
        method_dict = {"args": ", ".join(self.arguments)}
        method_dict.update(method.__dict__)
        method_dict["name"] = replace_operator_decl(method_dict["name"])
        method_str = config.method_decl % method_dict
        self.methods.append(method_str)
        self.arguments = []

    def visit_function(self, function):
        function_dict = {"args": ", ".join(self.arguments)}
        function_dict.update(function.__dict__)
        function_str = config.function_decl % function_dict
        self.output += (os.linesep * 2 + function_str + os.linesep)
        self.arguments = []

    def visit_param(self, param):
        self.arguments.append(config.arg_decl % param.__dict__)

    def export(self):
        return self.output


def replace_operator_decl(method_name):
    if method_name in config.call_operators:
        return "%s \"%s\"" % (config.call_operators[method_name], method_name)
    else:
        return method_name


class CythonImplementationExporter:
    """Export AST to Cython implementation file (.pyx).

    This class implements the visitor pattern.
    """
    def __init__(self, includes, type_info):
        self.includes = includes
        self.type_info = type_info
        self.output = ""
        self.ctors = []
        self.methods = []
        self.fields = []

    def visit_ast(self, ast):
        pass

    def visit_enum(self, enum):
        enum_def_dict = {}
        enum_def_dict.update(enum.__dict__)
        enum_def_dict["constants"] = indent_block(os.linesep.join(
            ["%s = cpp.%s" % (c, c) for c in enum.constants]), 1)
        self.output += config.enum_def % enum_def_dict + os.linesep

    def visit_typedef(self, typedef):
        pass

    def visit_field(self, field):
        try:
            setter_def = SetterDefinition(
                field, self.includes, self.type_info).make()
            getter_def = GetterDefinition(
                field, self.includes, self.type_info).make()
            field_def_parts = [config.field_def
                               % {"name": from_camel_case(field.name)},
                               indent_block(getter_def, 1),
                               indent_block(setter_def, 1)]
            self.fields.append(os.linesep.join(field_def_parts))
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring field '%s'" % field.name)

    def visit_class(self, clazz):
        if len(self.ctors) > 1:
            msg = ("Class '%s' has more than one constructor. This is not "
                   "compatible to Python. The last constructor will overwrite "
                   "all others." % clazz.name)
            warnings.warn(msg)
        elif len(self.ctors) == 0:
            self.ctors.append(config.ctor_default_def % clazz.__dict__)

        class_def_parts = [config.class_def % clazz.__dict__,
                           os.linesep.join(self.fields),
                           os.linesep.join(self.ctors),
                           os.linesep.join(self.methods)]

        class_def_parts = [p for p in class_def_parts if p != ""]
        self.output += os.linesep * 2 + os.linesep.join(class_def_parts)

        self.fields = []
        self.ctors = []
        self.methods = []

    def visit_constructor(self, ctor):
        try:
            function_def = ConstructorDefinition(
                ctor.class_name, ctor.arguments, self.includes,
                self.type_info).make()
            self.ctors.append(indent_block(function_def, 1))
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring method '%s'" % ctor.name)

    def visit_method(self, method):
        try:
            method_def = MethodDefinition(
                method.class_name, method.name, method.arguments, self.includes,
                method.result_type, self.type_info).make()
            self.methods.append(indent_block(method_def, 1))
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring method '%s'" % method.name)

    def visit_function(self, function):
        try:
            function_def = FunctionDefinition(
                function.name, function.arguments, self.includes,
                function.result_type, self.type_info).make()
            self.output += (os.linesep * 2 + function_def + os.linesep)
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring function '%s'" % function.name)

    def visit_param(self, param):
        pass

    def export(self):
        return self.output


class FunctionDefinition(object):
    def __init__(self, name, arguments, includes, result_type, type_info):
        self.name = name
        self.arguments = arguments
        self.includes = includes
        self.initial_args = []
        self.result_type = result_type
        self.type_info = type_info
        self.output_is_copy = True
        self._create_type_converters()

    def _create_type_converters(self):
        skip = 0
        self.type_converters = []
        for i, arg in enumerate(self.arguments):
            if skip > 0:
                skip -= 1
                continue
            type_converter = create_type_converter(
                arg.tipe, arg.name, self.type_info, (self.arguments, i))
            type_converter.add_includes(self.includes)
            self.type_converters.append(type_converter)
            skip = type_converter.n_cpp_args() - 1
        self.output_type_converter = create_type_converter(
            self.result_type, None, self.type_info)
        self.output_type_converter.add_includes(self.includes)

    def make(self):
        result = self._signature() + os.linesep
        body, call_args = self._input_type_conversions(self.includes)
        body += self._call_cpp_function(call_args)
        body += self.output_type_converter.return_output(self.output_is_copy)
        result += indent_block(body, 1)
        return result

    def _signature(self):
        function_name = from_camel_case(config.operators.get(
            self.name, self.name))
        signature_config = {
            "def": self._def_prefix(function_name),
            "name": function_name,
            "args": ", ".join(self._cython_signature_args())
        }
        return config.signature_def % signature_config

    def _def_prefix(self, function_name):
        special_method = (function_name.startswith("__") and
                          function_name.endswith("__"))
        if special_method:
            return "def"
        else:
            return "cpdef"

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

    def _call_cpp_function(self, call_args):
        cpp_type_decl = self.output_type_converter.cpp_type_decl()
        call = config.fun_call % {
            "name": self.name, "args": ", ".join(call_args)}
        return catch_result(cpp_type_decl, call) + os.linesep


class ConstructorDefinition(FunctionDefinition):
    def __init__(self, class_name, arguments, includes, type_info):
        super(ConstructorDefinition, self).__init__(
            "__init__", arguments, includes, result_type=None,
            type_info=type_info)
        self.initial_args = ["%s self" % class_name]
        self.class_name = class_name

    def _call_cpp_function(self, call_args):
        return config.ctor_call % {"class_name": self.class_name,
                                   "args": ", ".join(call_args)} + os.linesep


class MethodDefinition(FunctionDefinition):
    def __init__(self, class_name, name, arguments, includes, result_type,
                 type_info):
        super(MethodDefinition, self).__init__(
            name, arguments, includes, result_type, type_info)
        self.initial_args = ["%s self" % class_name]

    def _call_cpp_function(self, call_args):
        cpp_type_decl = self.output_type_converter.cpp_type_decl()
        call = config.method_call % {
            "name": config.call_operators.get(self.name, self.name),
            "args": ", ".join(call_args)}
        return catch_result(cpp_type_decl, call) + os.linesep


class SetterDefinition(MethodDefinition):
    def __init__(self, field, includes, type_info):
        name = "set_%s" % field.name
        super(SetterDefinition, self).__init__(
            field.class_name, name, [field], includes, "void", type_info)
        self.field_name = field.name

    def _call_cpp_function(self, call_args):
        assert len(call_args) == 1
        return config.setter_call % {"name": self.field_name,
                                     "call_arg": call_args[0]}


class GetterDefinition(MethodDefinition):
    def __init__(self, field, includes, type_info):
        name = "get_%s" % field.name
        super(GetterDefinition, self).__init__(
            field.class_name, name, [], includes, field.tipe, type_info)
        self.output_is_copy = False
        self.field_name = field.name

    def _call_cpp_function(self, call_args):
        assert len(call_args) == 0
        cpp_type_decl = self.output_type_converter.cpp_type_decl()
        call = config.getter_call % {"name": self.field_name}
        return catch_result(cpp_type_decl, call) + os.linesep


def catch_result(result_type_decl, call):
    if result_type_decl == "":
        return call
    else:
        return config.catch_result % {"cpp_type_decl": result_type_decl,
                                      "call": call}
