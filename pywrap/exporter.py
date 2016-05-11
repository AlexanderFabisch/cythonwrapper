import warnings
from functools import partial

from .template_specialization import (ClassSpecializer, FunctionSpecializer,
                                      MethodSpecializer)
from . import templates
from .ast import Constructor
from .templates import render
from .type_conversion import create_type_converter
from .utils import indent_block, from_camel_case


class CythonDeclarationExporter:
    """Export AST to Cython declaration file (.pxd).

    This class implements the visitor pattern.
    """
    def __init__(self, includes, config):
        self.includes = includes
        self.config = config
        self.typedefs = []
        self.enums = []
        self.functions = []
        self.classes = []
        self.fields = []
        self.ctors = []
        self.methods = []
        self.arguments = []
        self.output = None

    def visit_ast(self, ast):
        self.output = render("declarations", typedefs=self.typedefs,
                             enums=self.enums, functions=self.functions,
                             classes=self.classes)

    def visit_enum(self, enum):
        self.enums.append(render("enum_decl", **enum.__dict__))

    def visit_typedef(self, typedef):
        self.typedefs.append(templates.typedef_decl % typedef.__dict__)

    def visit_class(self, clazz):
        class_decl = {}
        class_decl.update(clazz.__dict__)
        class_decl["fields"] = self.fields
        class_decl["ctors"] = self.ctors
        class_decl["methods"] = self.methods
        class_decl["empty_body"] = (len(self.fields) + len(self.methods) +
                                    len(self.ctors) == 0)

        self.classes.append(render("class_decl", **class_decl))

        self.fields = []
        self.ctors = []
        self.methods = []

    def visit_field(self, field):
        if not field.ignored:
            self.fields.append(templates.field_decl % field.__dict__)

    def visit_constructor(self, ctor):
        if not ctor.ignored:
            const_dict = {"args": ", ".join(self.arguments)}
            const_dict.update(ctor.__dict__)
            const_str = templates.constructor_decl % const_dict
            self.ctors.append(const_str)
        self.arguments = []

    def visit_template_class(self, template_class):
        if not template_class.ignored:
            class_decl = {}
            class_decl.update(template_class.__dict__)
            class_decl["name"] = "%s[%s]" % (
                template_class.name, ", ".join(template_class.template_types))
            class_decl["fields"] = self.fields
            class_decl["ctors"] = self.ctors
            class_decl["methods"] = self.methods
            class_decl["empty_body"] = (len(self.fields) + len(self.methods) +
                                        len(self.ctors) == 0)

            self.classes.append(render("class_decl", **class_decl))

        self.fields = []
        self.ctors = []
        self.methods = []

    def visit_method(self, method):
        if not method.ignored:
            method_dict = {"args": ", ".join(self.arguments)}
            method_dict.update(method.__dict__)
            method_dict["name"] = replace_operator_decl(method_dict["name"],
                                                        self.config)
            method_str = templates.method_decl % method_dict
            self.methods.append(method_str)
        self.arguments = []

    def visit_template_method(self, template_method):
        if not template_method.ignored:
            method_dict = {"args": ", ".join(self.arguments),
                           "types": ", ".join(template_method.template_types)}
            method_dict.update(template_method.__dict__)
            method_dict["name"] = replace_operator_decl(method_dict["name"],
                                                        self.config)
            method_str = templates.template_method_decl % method_dict
            self.methods.append(method_str)
        self.arguments = []

    def visit_function(self, function):
        if not function.ignored:
            function_dict = {"args": ", ".join(self.arguments)}
            function_dict.update(function.__dict__)
            function_str = templates.function_decl % function_dict
            self.functions.append(function_str)
        self.arguments = []

    def visit_template_function(self, template_function):
        if not template_function.ignored:
            function_dict = {
                "args": ", ".join(self.arguments),
                "types": ", ".join(template_function.template_types)}
            function_dict.update(template_function.__dict__)
            function_str = templates.template_function_decl % function_dict
            self.functions.append(function_str)
        self.arguments = []

    def visit_param(self, param):
        self.arguments.append(templates.arg_decl % param.__dict__)

    def export(self):
        return self.output


def replace_operator_decl(method_name, config):
    if method_name in config.call_operators:
        return "%s \"%s\"" % (config.call_operators[method_name], method_name)
    else:
        return method_name


class CythonImplementationExporter:
    """Export AST to Cython implementation file (.pyx).

    This class implements the visitor pattern.
    """
    def __init__(self, includes, type_info, config):
        self.includes = includes
        self.type_info = type_info
        self.config = config
        self.enums = []
        self.functions = []
        self.classes = []
        self.fields = []
        self.ctors = []
        self.methods = []
        self.output = None

    def visit_ast(self, ast):
        self.output = render("definitions", enums=self.enums,
                             functions=self.functions, classes=self.classes)

    def visit_enum(self, enum):
        self.enums.append(render("enum", **enum.__dict__))

    def visit_typedef(self, typedef):
        pass

    def visit_class(self, clazz, cppname=None):
        if len(self.ctors) > 1:
            msg = ("Class '%s' has more than one constructor. This is not "
                   "compatible to Python. The last constructor will overwrite "
                   "all others." % clazz.name)
            warnings.warn(msg)
        elif len(self.ctors) == 0:
            self.ctors.append(Constructor(clazz.name))
        if cppname is None:
            cppname = clazz.name

        try:
            self.type_info.attach_specialization(clazz.get_attached_typeinfo())
            class_def = {}
            class_def.update(clazz.__dict__)
            class_def["cppname"] = cppname
            class_def["fields"] = map(partial(
                self._process_field, selftype=clazz.name), self.fields)
            class_def["ctors"] = map(partial(
                self._process_constructor, selftype=clazz.name,
                cpptype=clazz.get_cppname()),
                                     self.ctors)
            class_def["methods"] = map(partial(
                self._process_method, selftype=clazz.name), self.methods)
        finally:
            self.type_info.remove_specialization()


        self.classes.append(render("class", **class_def))

        self.fields = []
        self.ctors = []
        self.methods = []

    def visit_template_class(self, template_class):
        specializer = ClassSpecializer(self.config)
        for clazz in specializer.specialize(template_class):
            self.visit_class(clazz, cppname=clazz.get_cppname())

    def visit_field(self, field):
        self.fields.append(field)

    def _process_field(self, field, selftype):
        try:
            setter_def = SetterDefinition(
                selftype, field, self.includes, self.type_info,
                self.config).make()
            getter_def = GetterDefinition(
                selftype, field, self.includes, self.type_info,
                self.config).make()
            return {
                "name": from_camel_case(field.name),
                "getter": indent_block(getter_def, 1),
                "setter": indent_block(setter_def, 1)
            }
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring field '%s'" % field.name)
            field.ignored = True
            return {}

    def visit_constructor(self, ctor):
        self.ctors.append(ctor)

    def _process_constructor(self, ctor, selftype, cpptype):
        try:
            constructor_def = ConstructorDefinition(
                selftype, ctor.arguments, self.includes,
                self.type_info, self.config, cpptype).make()
            return indent_block(constructor_def, 1)
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring method '%s'" % ctor.name)
            ctor.ignored = True
            return ""

    def visit_method(self, method, cppname=None):
        self.methods.append((method, cppname))

    def _process_method(self, arg, selftype):
        method, cppname = arg
        try:
            method_def = MethodDefinition(
                selftype, method.name, method.arguments, self.includes,
                method.result_type, self.type_info, self.config,
                cppname=cppname).make()
            return indent_block(method_def, 1)
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring method '%s'" % method.name)
            method.ignored = True
            return ""

    def visit_template_method(self, template_method):
        specializer = MethodSpecializer(self.config)
        for method in specializer.specialize(template_method):
            self.visit_method(method, cppname=template_method.name)

    def visit_function(self, function, cppname=None):
        try:
            self.functions.append(FunctionDefinition(
                function.name, function.arguments, self.includes,
                function.result_type, self.type_info,
                self.config, cppname=cppname).make())
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring function '%s'" % function.name)
            function.ignored = True

    def visit_template_function(self, template_function):
        specializer = FunctionSpecializer(self.config)
        for method in specializer.specialize(template_function):
            self.visit_function(method, cppname=template_function.name)

    def visit_param(self, param):
        pass

    def export(self):
        return self.output


class FunctionDefinition(object):
    def __init__(self, name, arguments, includes, result_type, type_info,
                 config, cppname=None):
        self.name = name
        self.arguments = arguments
        self.includes = includes
        self.initial_args = []
        self.result_type = result_type
        self.type_info = type_info
        self.config = config
        if cppname is None:
            self.cppname = self.name
        else:
            self.cppname = cppname
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
                arg.tipe, arg.name, self.type_info, self.config,
                (self.arguments, i))
            type_converter.add_includes(self.includes)
            self.type_converters.append(type_converter)
            skip = type_converter.n_cpp_args() - 1
        self.output_type_converter = create_type_converter(
            self.result_type, None, self.type_info, self.config)
        self.output_type_converter.add_includes(self.includes)

    def make(self):
        function = self._signature()
        function["input_conversions"], call_args = self._input_type_conversions(
            self.includes)
        function["call"] = self._call_cpp_function(call_args)
        function["return_output"] = self.output_type_converter.return_output(
            self.output_is_copy)
        return render("function", **function)

    def _signature(self):
        function_name = from_camel_case(
            self.config.cpp_to_py_operator(self.name))
        return {"def_prefix": self._def_prefix(function_name),
                "args": ", ".join(self._cython_signature_args()),
                "name": function_name}

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
        conversions = []
        call_args = []
        for type_converter in self.type_converters:
            conversions.append(type_converter.python_to_cpp())
            call_args.extend(type_converter.cpp_call_args())
        return conversions, call_args

    def _call_cpp_function(self, call_args):
        cpp_type_decl = self.output_type_converter.cpp_type_decl()
        call = templates.fun_call % {"name": self.cppname,
                                     "call_args": ", ".join(call_args)}
        return catch_result(cpp_type_decl, call)


class ConstructorDefinition(FunctionDefinition):
    def __init__(self, class_name, arguments, includes, type_info, config,
                 cpp_classname):
        super(ConstructorDefinition, self).__init__(
            "__init__", arguments, includes, result_type=None,
            type_info=type_info, config=config)
        self.initial_args = ["%s self" % class_name]
        self.cpp_classname = cpp_classname

    def _call_cpp_function(self, call_args):
        return templates.ctor_call % {"class_name": self.cpp_classname,
                                      "call_args": ", ".join(call_args)}


class MethodDefinition(FunctionDefinition):
    def __init__(self, class_name, name, arguments, includes, result_type,
                 type_info, config, cppname=None):
        super(MethodDefinition, self).__init__(
            name, arguments, includes, result_type, type_info, config, cppname)
        self.initial_args = ["%s self" % class_name]

    def _call_cpp_function(self, call_args):
        cpp_type_decl = self.output_type_converter.cpp_type_decl()
        call = templates.method_call % {
            "name": self.config.call_operators.get(self.cppname, self.cppname),
            "call_args": ", ".join(call_args)}
        return catch_result(cpp_type_decl, call)


class SetterDefinition(MethodDefinition):
    def __init__(self, class_name, field, includes, type_info, config):
        name = "set_%s" % field.name
        super(SetterDefinition, self).__init__(
            class_name, name, [field], includes, "void", type_info, config)
        self.field_name = field.name

    def _call_cpp_function(self, call_args):
        assert len(call_args) == 1
        return templates.setter_call % {"name": self.field_name,
                                        "call_args": call_args[0]}


class GetterDefinition(MethodDefinition):
    def __init__(self, class_name, field, includes, type_info, config):
        name = "get_%s" % field.name
        super(GetterDefinition, self).__init__(
            class_name, name, [], includes, field.tipe, type_info, config)
        self.output_is_copy = False
        self.field_name = field.name

    def _call_cpp_function(self, call_args):
        assert len(call_args) == 0
        cpp_type_decl = self.output_type_converter.cpp_type_decl()
        call = templates.getter_call % {"name": self.field_name}
        return catch_result(cpp_type_decl, call)


def catch_result(result_type_decl, call):
    if result_type_decl == "":
        return call
    else:
        return templates.catch_result % {"cpp_type_decl": result_type_decl,
                                         "call": call}
