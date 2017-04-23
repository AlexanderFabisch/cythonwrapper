import os
import warnings

from .utils import indent_block, from_camel_case


class AstNode(object):
    def __init__(self):
        self.nodes = []
        self.ignored = False

    def accept(self, exporter):
        for node in self.nodes:
            node.accept(exporter)
        method_name = "visit_" + from_camel_case(self.__class__.__name__)
        visit_method = getattr(exporter, method_name)
        visit_method(self)


class Ast(AstNode):
    """Abstract Syntax Tree."""
    def __init__(self):
        super(Ast, self).__init__()

    def __str__(self):
        result = "AST"
        if len(self.nodes) > 0:
            result += os.linesep + indent_block(os.linesep.join(
                [str(node) for node in self.nodes]), 1)
        return result


class Enum(AstNode):
    def __init__(self, filename, namespace, tipe, comment=""):
        super(Enum, self).__init__()
        self.filename = filename
        self.namespace = namespace
        self.tipe = tipe
        self.comment = comment
        self.constants = []

    def __str__(self):
        return "Enum '%s'" % self.tipe


class Typedef(AstNode):
    def __init__(self, filename, namespace, tipe, underlying_type):
        super(Typedef, self).__init__()
        self.filename = filename
        self.namespace = namespace
        self.tipe = tipe
        self.underlying_type = underlying_type

    def __str__(self):
        return "Typedef (%s) %s" % (self.underlying_type, self.tipe)


class Clazz(AstNode):
    def __init__(self, filename, namespace, name, comment=""):
        super(Clazz, self).__init__()
        self.filename = filename
        self.namespace = namespace
        self.name = name
        self.comment = comment
        self.base = None

    def __str__(self):
        result = "%s '%s' ('%s')" % (
            self.__class__.__name__.replace("zz", "ss"),
            self.name, self.get_cppname())
        if self.base is not None:
            result += " extends '%s'" % self.base
        if self.namespace != "":
            result += " (namespace: '%s')" % self.namespace
        if len(self.nodes) > 0:
            result += os.linesep + indent_block(os.linesep.join(
                [str(node) for node in self.nodes]), 1)
        return result

    def get_cppname(self):
        return self.name

    def get_attached_typeinfo(self):
        return {}


class TemplateClazzSpecialization(Clazz):
    def __init__(self, filename, namespace, name, cppname, specialization,
                 comment=""):
        super(TemplateClazzSpecialization, self).__init__(
            filename, namespace, name, comment)
        self.cppname = cppname
        self.specialization = specialization

    def get_cppname(self):
        return self.cppname

    def get_attached_typeinfo(self):
        return self.specialization


class FunctionBase(AstNode):
    def __init__(self, name, comment=""):
        super(FunctionBase, self).__init__()
        self.name = name
        self.comment = comment

    def __str__(self):
        result = "%s '%s'" % (self.__class__.__name__, self.name)
        if len(self.nodes) > 0:
            result += os.linesep + indent_block(os.linesep.join(
                [str(arg) for arg in self.nodes]), 1)
        return result


class Function(FunctionBase):
    def __init__(self, filename, namespace, name, result_type, comment=""):
        super(Function, self).__init__(name, comment)
        self.filename = filename
        self.namespace = namespace
        self.result_type = result_type

    def __str__(self):
        result = super(Function, self).__str__()
        if self.result_type != "void":
            result += os.linesep + indent_block(
                "Returns (%s)" % self.result_type, 1)
        return result


class Constructor(FunctionBase):
    def __init__(self, class_name, comment=""):
        super(Constructor, self).__init__("__init__", comment)
        self.class_name = class_name


class Method(FunctionBase):
    def __init__(self, name, result_type, class_name, comment=""):
        super(Method, self).__init__(name, comment)
        self.result_type = result_type
        self.class_name = class_name

    def __str__(self):
        result = super(Method, self).__str__()
        if self.result_type != "void":
            result += os.linesep + indent_block(
                "Returns (%s)" % self.result_type, 1)
        return result


class Template:
    def __init__(self):
        self.template_types = []

    def __str__(self):
        return indent_block(os.linesep.join(
            ["Template type '%s'" % tt for tt in self.template_types]), 1)


class TemplateClass(Clazz, Template):
    def __init__(self, filename, namespace, name, comment=""):
        Clazz.__init__(self, filename, namespace, name, comment)
        Template.__init__(self)

    def __str__(self):
        result = Clazz.__str__(self)
        result += os.linesep + Template.__str__(self)
        return result


class TemplateFunction(Function, Template):
    def __init__(self, filename, namespace, name, result_type, comment=""):
        Function.__init__(self, filename, namespace, name, result_type, comment)
        Template.__init__(self)

    def __str__(self):
        result = Function.__str__(self)
        result += os.linesep + Template.__str__(self)
        return result


class TemplateMethod(Method, Template):
    def __init__(self, name, result_type, class_name, comment=""):
        Method.__init__(self, name, result_type, class_name, comment)
        Template.__init__(self)

    def __str__(self):
        result = Method.__str__(self)
        result += os.linesep + Template.__str__(self)
        return result


class Param(AstNode):
    def __init__(self, name, tipe):
        super(Param, self).__init__()
        self.name = name
        self.tipe = tipe
        self.default_value = None

    def __str__(self):
        result = "Parameter (%s) %s" % (self.tipe, self.name)
        if self.default_value is not None:
            result += " = " + str(self.default_value)
        return result


class Field(AstNode):
    def __init__(self, name, tipe, class_name, comment=""):
        super(Field, self).__init__()
        self.name = name
        self.tipe = tipe
        self.class_name = class_name
        self.comment = comment

    def __str__(self):
        return "Field (%s) %s" % (self.tipe, self.name)


def handle_inheritance(asts):
    classes = {}
    for ast in asts:
        for n in ast.nodes:
            if isinstance(n, Clazz):
                classes[n.name] = n

    leaf_names = set()
    for clazz in classes.values():
        leaf_names.add(clazz.name)
        if clazz.base is not None:
            if clazz.base in leaf_names:
                leaf_names.remove(clazz.base)

    for leaf_name in leaf_names:
        _copy_methods_recursive(classes, classes[leaf_name])

    # TODO extract method
    for clazz in classes.values():
        methods = [n for n in clazz.nodes if isinstance(n, Method)]
        method_names = []
        removed_methods = []
        for m in methods:
            if m.name in method_names:
                warnings.warn(
                    "Method '%s.%s' is already defined. Only one method "
                    "will be exposed." % (clazz.name, m.name))
                removed_methods.append(m)
            else:
                method_names.append(m.name)
        clazz.nodes = [n for n in clazz.nodes if n not in removed_methods]

    functions = [n for ast in asts for n in ast.nodes
                 if isinstance(n, Function)]
    function_names = []
    removed_functions = []
    for f in functions:
        if f.name in function_names:
            warnings.warn(
                "Function '%s' is already defined. Only one method "
                "will be exposed." % f.name)
            removed_functions.append(f)
        else:
            function_names.append(f.name)
    for ast in asts:
        ast.nodes = [n for n in ast.nodes if n not in removed_functions]


def _copy_methods_recursive(classes, clazz):
    if clazz.base is not None:
        base_methods = _copy_methods_recursive(classes, classes[clazz.base])
        unique_methods = set([n.name for n in clazz.nodes
                              if isinstance(n, Method)])
        base_methods = [m for m in base_methods if m.name not in unique_methods]
        clazz.nodes.extend(base_methods)
    return [node for node in clazz.nodes if isinstance(node, Method)]
