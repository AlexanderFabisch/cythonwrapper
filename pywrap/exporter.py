import warnings
from functools import partial
from itertools import chain
from abc import ABCMeta, abstractmethod

from . import templates
from .ast import Constructor
from .parser import Includes, TypeInfo
from .defaultconfig import Config
from .template_specialization import (ClassSpecializer, FunctionSpecializer,
                                      MethodSpecializer)
from .templates import render
from .type_conversion import create_type_converter
from .utils import from_camel_case, replace_keyword_argnames


class AstExporter(object):
    """Base class of AST exporters.

    An AST exporter converts elements of an AST to a single string. This
    is an implementation of the visitor pattern to avoid duplication in the
    code that walks through the AST.
    """
    __metaclass__ = ABCMeta
    def __init__(self):
        self.typedefs = []
        self.enums = []
        self.functions = []
        self.classes = []
        self.arguments = []
        self._clear_class()

        self.output = None

    def _clear_class(self):
        """Set collected class members to empty list."""
        self.fields = []
        self.ctors = []
        self.methods = []

    def export(self):
        """Export generated string.

        Returns
        -------
        output : str
            Generated output
        """
        return self.output

    @abstractmethod
    def visit_ast(self, ast):
        """Visit AST.

        Parameters
        ----------
        ast : AST
            Abstract syntax tree
        """

    @abstractmethod
    def visit_enum(self, enum):
        """Visit enum.

        Parameters
        ----------
        enum : Enum
            Enumeration
        """

    @abstractmethod
    def visit_typedef(self, typedef):
        """Visit typedef.

        Parameters
        ----------
        typedef : Typedef
            Type definition
        """

    @abstractmethod
    def visit_clazz(self, clazz):
        """Visit class.

        Parameters
        ----------
        clazz : Clazz
            Custom class
        """

    @abstractmethod
    def visit_field(self, field):
        """Visit field.

        Parameters
        ----------
        field : Field
            Field, data member of a class
        """

    @abstractmethod
    def visit_constructor(self, ctor):
        """Visit constructor.

        Parameters
        ----------
        ctor : Constructor
            Class constructor
        """

    @abstractmethod
    def visit_template_class(self, template_class):
        """Visit template class.

        Parameters
        ----------
        template_class : TemplateClass
            Template class
        """

    @abstractmethod
    def visit_method(self, method):
        """Visit method.

        Parameters
        ----------
        method : Method
            Visit class method
        """

    @abstractmethod
    def visit_template_method(self, template_method):
        """Visit template method.

        Parameters
        ----------
        template_method : TemplateMethod
            Template method that defines its own template type(s)
        """

    @abstractmethod
    def visit_function(self, function):
        """Visit function.

        Parameters
        ----------
        function : Function
            Function that does not belong to a class
        """

    @abstractmethod
    def visit_template_function(self, template_function):
        """Visit template function.

        Parameters
        ----------
        template_function : TemplateFunction
            Template function
        """

    @abstractmethod
    def visit_param(self, param):
        """Visit function parameter.

        Parameters
        ----------
        param : Param
            A parameter of a constructor, method, or function
        """


class CythonDeclarationExporter(AstExporter):
    """Export to Cython declaration file (.pxd).

    Parameters
    ----------
    includes : Includes, optional
        Collects information about required import statements from the exporter

    config : Config, optional
        Configuration that controls e.g. template specializations
    """
    def __init__(self, includes=Includes(), config=Config()):
        super(CythonDeclarationExporter, self).__init__()
        self.includes = includes
        self.config = config

    def visit_ast(self, ast):
        self.output = render("declarations", typedefs=self.typedefs,
                             enums=self.enums, functions=self.functions,
                             classes=self.classes)

    def visit_enum(self, enum):
        self.enums.append(render("enum_decl", enum=enum))

    def visit_typedef(self, typedef):
        self.typedefs.append(templates.typedef_decl % typedef.__dict__)

    def visit_clazz(self, clazz):
        self._visit_class(clazz)

    def visit_template_class(self, template_class):
        name = "%s[%s]" % (template_class.name,
                           ", ".join(template_class.template_types))
        self._visit_class(template_class, {"name": name})

    def _visit_class(self, clazz, additional_args=None):
        if not clazz.ignored:
            class_decl = {}
            class_decl.update(clazz.__dict__)
            if additional_args is not None:
                class_decl.update(additional_args)
            class_decl["fields"] = self.fields
            class_decl["ctors"] = self.ctors
            class_decl["methods"] = self.methods
            class_decl["empty_body"] = (len(self.fields) + len(self.methods) +
                                        len(self.ctors) == 0)

            self.classes.append(render("class_decl", **class_decl))
        self._clear_class()

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
        self._visit_method(method, templates.method_decl)

    def visit_template_method(self, template_method):
        self._visit_method(
            template_method, templates.template_method_decl,
            {"types": ", ".join(template_method.template_types)})

    def _visit_method(self, method, template, additional_args=None):
        if not method.ignored:
            method_dict = {"args": ", ".join(self.arguments)}
            method_dict.update(method.__dict__)
            if additional_args is not None:
                method_dict.update(additional_args)
            method_dict["name"] = replace_operator_decl(
                method_dict["name"], self.config)
            method_str = template % method_dict
            method_str += self._exception_suffix(method.result_type)
            self.methods.append(method_str)
        self.arguments = []

    def visit_function(self, function):
        if not function.ignored:
            function_dict = {"args": ", ".join(self.arguments)}
            function_dict.update(function.__dict__)
            function_str = templates.function_decl % function_dict
            function_str += self._exception_suffix(function.result_type)
            self.functions.append(function_str)
        self.arguments = []

    def visit_template_function(self, template_function):
        if not template_function.ignored:
            function_dict = {
                "args": ", ".join(self.arguments),
                "types": ", ".join(template_function.template_types)}
            function_dict.update(template_function.__dict__)
            function_str = templates.template_function_decl % function_dict
            function_str += self._exception_suffix(
                template_function.result_type)
            self.functions.append(function_str)
        self.arguments = []

    def visit_param(self, param):
        param_dict = param.__dict__
        param_dict["name"] = replace_keyword_argnames(param.name)
        self.arguments.append(templates.arg_decl % param_dict)

    def _exception_suffix(self, result_type):
        """Workaround for bug in Cython when returning C arrays."""
        if result_type == "char *":
            return ""
        else:
            return " except +"


def replace_operator_decl(method_name, config):
    if method_name in config.call_operators:
        return "%s \"%s\"" % (config.call_operators[method_name], method_name)
    else:
        return method_name


class CythonImplementationExporter(AstExporter):
    """Export to Cython implementation file (.pyx).

    Parameters
    ----------
    includes : Includes, optional
        Collects information about required import statements from the exporter

    type_info : TypeInfo, optional
        Contains names of custom C++ types that have been defined in the code

    config : Config, optional
        Configuration that controls e.g. template specializations
    """
    def __init__(self, includes=Includes(), type_info=TypeInfo(),
                 config=Config()):
        super(CythonImplementationExporter, self).__init__()
        self.includes = includes
        self.type_info = type_info
        self.config = config

    def export(self):
        return super(CythonImplementationExporter, self).export()

    def visit_ast(self, ast):
        self.output = render("definitions", enums=self.enums,
                             functions=self.functions, classes=self.classes)

    def visit_enum(self, enum):
        self.enums.append(render("enum", enum=enum))

    def visit_typedef(self, typedef):
        pass

    def visit_clazz(self, clazz, cppname=None):
        if self.config.is_ignored_class(clazz.filename, clazz.name):
            warnings.warn("Class '%s' from file '%s' is on the blacklist and "
                          "will be ignored." % (clazz.name, clazz.filename))
            clazz.ignored = True
            self._clear_class()
            return

        if len(self.ctors) > 1:
            msg = ("Class '%s' has more than one constructor. This is not "
                   "compatible to Python. The last constructor will overwrite "
                   "all others." % clazz.name)
            warnings.warn(msg)
        elif len(self.ctors) == 0:
            self.ctors.append(Constructor(clazz.name, ""))
        if cppname is None:
            cppname = clazz.name

        self.type_info.attach_specialization(clazz.get_attached_typeinfo())
        class_def = {}
        class_def.update(clazz.__dict__)
        class_def["cppname"] = cppname
        class_def["comment"] = clazz.comment
        class_def["fields"] = map(partial(
            self._process_field, selftype=clazz.name), self.fields)
        class_def["ctors"] = map(partial(
            self._process_constructor, selftype=clazz.name,
            cpptype=clazz.get_cppname()), self.ctors)
        class_def["methods"] = map(partial(
            self._process_method, selftype=clazz.name), self.methods)

        self.classes.append(render("class", **class_def))
        self._clear_class()

    def visit_template_class(self, template_class):
        specializer = ClassSpecializer(self.config)
        for clazz in specializer.specialize(template_class):
            self.visit_clazz(clazz, cppname=clazz.get_cppname())

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
                "getter": getter_def,
                "setter": setter_def
            }
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring field '%s'" % field.name)
            field.ignored = True
            return {}

    def visit_constructor(self, ctor):
        self.ctors.append(ctor)

    def _process_constructor(self, ctor, selftype, cpptype):
        if self.config.is_abstract_class(ctor.class_name):
            warnings.warn("Class '%s' is abstract and will have no constructor."
                          % ctor.class_name)
            ctor.ignored = True
            return ""

        try:
            constructor_def = ConstructorDefinition(
                selftype, ctor.comment, ctor.nodes, self.includes,
                self.type_info, self.config, cpptype)
            return constructor_def.make()
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring method '%s'" % ctor.name)
            ctor.ignored = True
            return ""

    def visit_method(self, method, cppname=None):
        if self.config.is_ignored_method(method.class_name, method.name):
            warnings.warn("Method '%s::%s' is on the blacklist and will be "
                          "ignored." % (method.class_name, method.name))
            method.ignored = True
            return

        self.methods.append((method, cppname))

    def _process_method(self, arg, selftype):
        method, cppname = arg
        try:
            method_def = MethodDefinition(
                selftype, method.comment, method.name, method.nodes,
                self.includes, method.result_type, self.type_info, self.config,
                cppname=cppname)
            return method_def.make()
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
                function.name, function.comment, function.nodes, self.includes,
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


class FunctionDefinition(object):
    def __init__(self, name, comment, arguments, includes, result_type,
                 type_info, config, cppname=None):
        self.name = name
        self.comment = comment
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
        function["input_conversions"] = self._input_type_conversions()
        function["call"] = self._call_cpp_function(self._call_args())
        function["return_output"] = self.output_type_converter.return_output(
            self.output_is_copy)
        function["comment"] = self.comment
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
        return self.initial_args + [tc.python_type_decl()
                                    for tc in self.type_converters]

    def _input_type_conversions(self):
        return [tc.python_to_cpp() for tc in self.type_converters]

    def _call_args(self):
        return list(chain.from_iterable(
            tc.cpp_call_args() for tc in self.type_converters))

    def _call_cpp_function(self, call_args):
        call = templates.fun_call % {"name": self.cppname,
                                     "call_args": ", ".join(call_args)}
        return catch_result(self.output_type_converter.cpp_type_decl(), call)


class ConstructorDefinition(FunctionDefinition):
    def __init__(self, class_name, comment, arguments, includes, type_info,
                 config, cpp_classname):
        super(ConstructorDefinition, self).__init__(
            "__init__", comment, arguments, includes, result_type=None,
            type_info=type_info, config=config)
        self.initial_args = ["%s self" % class_name]
        self.cpp_classname = cpp_classname

    def _call_cpp_function(self, call_args):
        return templates.ctor_call % {"class_name": self.cpp_classname,
                                      "call_args": ", ".join(call_args)}


class MethodDefinition(FunctionDefinition):
    def __init__(self, class_name, comment, name, arguments, includes,
                 result_type, type_info, config, cppname=None):
        super(MethodDefinition, self).__init__(
            name, comment, arguments, includes, result_type, type_info, config, cppname)
        self.initial_args = ["%s self" % class_name]

    def _call_cpp_function(self, call_args):
        call = templates.method_call % {
            "name": self.config.call_operators.get(self.cppname, self.cppname),
            "call_args": ", ".join(call_args)}
        return catch_result(self.output_type_converter.cpp_type_decl(), call)


class SetterDefinition(MethodDefinition):
    def __init__(self, python_classname, field, includes, type_info, config):
        name = "set_%s" % field.name
        super(SetterDefinition, self).__init__(
            python_classname, "", name, [field], includes, "void", type_info,
            config)
        self.field_name = field.name

    def _call_cpp_function(self, call_args):
        assert len(call_args) == 1
        return templates.setter_call % {"name": self.field_name,
                                        "call_args": call_args[0]}


class GetterDefinition(MethodDefinition):
    def __init__(self, python_classname, field, includes, type_info, config):
        name = "get_%s" % field.name
        super(GetterDefinition, self).__init__(
            python_classname, "", name, [], includes, field.tipe, type_info,
            config)
        self.output_is_copy = False
        self.field_name = field.name

    def _call_cpp_function(self, call_args):
        assert len(call_args) == 0
        call = templates.getter_call % {"name": self.field_name}
        return catch_result(self.output_type_converter.cpp_type_decl(), call)


def catch_result(result_type_decl, call):
    if result_type_decl == "":
        return call
    else:
        return templates.catch_result % {"cpp_type_decl": result_type_decl,
                                         "call": call}
