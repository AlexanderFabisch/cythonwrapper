import warnings

from . import templates
from .ast import Method, Function, Param
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

    def visit_class(self, clazz):
        if len(self.ctors) > 1:
            msg = ("Class '%s' has more than one constructor. This is not "
                   "compatible to Python. The last constructor will overwrite "
                   "all others." % clazz.name)
            warnings.warn(msg)
        elif len(self.ctors) == 0:
            self.ctors.append(templates.ctor_default_def % clazz.__dict__)

        class_def = {}
        class_def.update(clazz.__dict__)
        class_def["fields"] = self.fields
        class_def["ctors"] = self.ctors
        class_def["methods"] = self.methods

        self.classes.append(render("class", **class_def))

        self.fields = []
        self.ctors = []
        self.methods = []

    def visit_field(self, field):
        try:
            setter_def = SetterDefinition(
                field, self.includes, self.type_info, self.config).make()
            getter_def = GetterDefinition(
                field, self.includes, self.type_info, self.config).make()
            self.fields.append({
                "name": from_camel_case(field.name),
                "getter": indent_block(getter_def, 1),
                "setter": indent_block(setter_def, 1)
            })
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring field '%s'" % field.name)
            field.ignored = True

    def visit_constructor(self, ctor):
        try:
            constructor_def = ConstructorDefinition(
                ctor.class_name, ctor.arguments, self.includes,
                self.type_info, self.config).make()
            self.ctors.append(indent_block(constructor_def, 1))
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring method '%s'" % ctor.name)
            ctor.ignored = True

    def visit_method(self, method, cppname=None):
        try:
            method_def = MethodDefinition(
                method.class_name, method.name, method.arguments, self.includes,
                method.result_type, self.type_info, self.config,
                cppname=cppname).make()
            self.methods.append(indent_block(method_def, 1))
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring method '%s'" % method.name)
            method.ignored = True

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


class Specializer(object):
    def __init__(self, config):
        self.config = config

    def specialize(self, general):
        try:
            specs = self._lookup_specification(general)
        except LookupError as e:
            warnings.warn(e.message)
            general.ignored = True
            return []

        return self._specialize(general, specs)

    def _lookup_specification(self, general):
        key = self._key(general)
        if key not in self.config.registered_template_specializations:
            raise LookupError(
                "No template specialization registered for template method "
                "'%s' with the following template types: %s"
                % (key, ", ".join(general.template_types)))
        return self.config.registered_template_specializations[key]

    def _key(self, general):
        raise NotImplementedError()

    def _replace_specification(self, tipe, spec):
        return spec.get(tipe, tipe)

    def _specialize(self, general, specs):
        raise NotImplementedError()


class FunctionSpecializer(Specializer):
    """Convert a template method to a method."""

    def __init__(self, config):
        super(FunctionSpecializer, self).__init__(config)

    def _key(self, general):
        if general.namespace != "":
            return "%s::%s" % (general.namespace, general.name)
        else:
            return general.name

    def _specialize(self, general, specs):
        specialized_functions = []
        for name, spec in specs:
            result_type = self._replace_specification(general.result_type, spec)

            specialized = Function(general.filename, general.namespace, name,
                                   result_type)

            for arg in general.arguments:
                tipe = self._replace_specification(arg.tipe, spec)
                specialized.arguments.append(Param(arg.name, tipe))

            specialized_functions.append(specialized)
        return specialized_functions


class MethodSpecializer(Specializer):
    """Convert a template method to a method."""
    def __init__(self, config):
        super(MethodSpecializer, self).__init__(config)

    def _key(self, general):
        return "%s::%s" % (general.class_name, general.name)

    def _specialize(self, general, specs):
        specialized_methods = []
        for name, spec in specs:
            result_type = self._replace_specification(general.result_type, spec)

            specialized = Method(name, result_type, general.class_name)

            for arg in general.arguments:
                tipe = self._replace_specification(arg.tipe, spec)
                specialized.arguments.append(Param(arg.name, tipe))

            specialized_methods.append(specialized)
        return specialized_methods


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
    def __init__(self, class_name, arguments, includes, type_info, config):
        super(ConstructorDefinition, self).__init__(
            "__init__", arguments, includes, result_type=None,
            type_info=type_info, config=config)
        self.initial_args = ["%s self" % class_name]
        self.class_name = class_name

    def _call_cpp_function(self, call_args):
        return templates.ctor_call % {"class_name": self.class_name,
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
    def __init__(self, field, includes, type_info, config):
        name = "set_%s" % field.name
        super(SetterDefinition, self).__init__(
            field.class_name, name, [field], includes, "void", type_info,
            config)
        self.field_name = field.name

    def _call_cpp_function(self, call_args):
        assert len(call_args) == 1
        return templates.setter_call % {"name": self.field_name,
                                        "call_args": call_args[0]}


class GetterDefinition(MethodDefinition):
    def __init__(self, field, includes, type_info, config):
        name = "get_%s" % field.name
        super(GetterDefinition, self).__init__(
            field.class_name, name, [], includes, field.tipe, type_info, config)
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
