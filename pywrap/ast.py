import os

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
    def __init__(self, filename, namespace, tipe, comment):
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
    def __init__(self, filename, namespace, name, comment):
        super(Clazz, self).__init__()
        self.filename = filename
        self.namespace = namespace
        self.name = name
        self.comment = comment

    def __str__(self):
        result = "%s '%s' ('%s')" % (
            self.__class__.__name__.replace("zz", "ss"),
            self.name, self.get_cppname())
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
                 comment):
        super(TemplateClazzSpecialization, self).__init__(
            filename, namespace, name, comment)
        self.cppname = cppname
        self.specialization = specialization

    def get_cppname(self):
        return self.cppname

    def get_attached_typeinfo(self):
        return self.specialization


class FunctionBase(AstNode):
    def __init__(self, name, comment):
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
    def __init__(self, filename, namespace, name, result_type, comment):
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
    def __init__(self, class_name, comment):
        super(Constructor, self).__init__("__init__", comment)
        self.class_name = class_name


class Method(FunctionBase):
    def __init__(self, name, result_type, class_name, comment):
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
    def __init__(self, filename, namespace, name, comment):
        Clazz.__init__(self, filename, namespace, name, comment)
        Template.__init__(self)

    def __str__(self):
        result = Clazz.__str__(self)
        result += os.linesep + Template.__str__(self)
        return result


class TemplateFunction(Function, Template):
    def __init__(self, filename, namespace, name, result_type, comment):
        Function.__init__(self, filename, namespace, name, result_type, comment)
        Template.__init__(self)

    def __str__(self):
        result = Function.__str__(self)
        result += os.linesep + Template.__str__(self)
        return result


class TemplateMethod(Method, Template):
    def __init__(self, name, result_type, class_name, comment):
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
    def __init__(self, name, tipe, class_name, comment):
        super(Field, self).__init__()
        self.name = name
        self.tipe = tipe
        self.class_name = class_name
        self.comment = comment

    def __str__(self):
        return "Field (%s) %s" % (self.tipe, self.name)
