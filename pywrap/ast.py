import os
from .utils import indent_block


class AST:
    """Abstract Syntax Tree."""
    def __init__(self):
        self.functions = []
        self.classes = []
        self.typedefs = []
        self.enums = []

    def accept(self, exporter):
        for enum in self.enums:
            enum.accept(exporter)
        for typedef in self.typedefs:
            typedef.accept(exporter)
        for clazz in self.classes:
            clazz.accept(exporter)
        for fun in self.functions:
            fun.accept(exporter)
        exporter.visit_ast(self)

    def __str__(self):
        result = "AST"
        if len(self.enums) > 0:
            result += os.linesep + indent_block(os.linesep.join(
                [str(enum) for enum in self.enums]), 1)
        if len(self.typedefs) > 0:
            result += os.linesep + indent_block(os.linesep.join(
                [str(typedef) for typedef in self.typedefs]), 1)
        if len(self.classes) > 0:
            result += os.linesep + indent_block(os.linesep.join(
                [str(clazz) for clazz in self.classes]), 1)
        if len(self.functions) > 0:
            result += os.linesep + indent_block(os.linesep.join(
                [str(fun) for fun in self.functions]), 1)
        return result


class Includes:
    def __init__(self):
        self.numpy = False
        self.stl = {"vector": False,
                    "string": False,
                    "deque": False,
                    "list": False,
                    "map": False,
                    "pair": False,
                    "queue": False,
                    "set": False,
                    "stack": False}
        self.deref = False

    def add_include_for(self, tname):
        if self._part_of_tname(tname, "bool"):
            self.boolean = True
        for t in self.stl.keys():
            if self._part_of_tname(tname, t):
                self.stl[t] = True

    def add_include_for_deref(self):
        self.deref = True

    def _part_of_tname(self, tname, subtname):
        return (tname == subtname or tname.startswith(subtname) or
                ("<" + subtname + ">") in tname or
                ("<" + subtname + ",") in tname or
                (", " + subtname + ">") in tname or
                ("[" + subtname + "]") in tname or
                ("[" + subtname + ",") in tname or
                (", " + subtname + "]") in tname)

    def declarations_import(self):
        includes = "from libcpp cimport bool" + os.linesep

        for t in self.stl.keys():
            if self.stl[t]:
                includes += ("from libcpp.%(type)s cimport %(type)s"
                             % {"type": t}) + os.linesep

        return includes

    def implementations_import(self):
        includes = "from libcpp cimport bool" + os.linesep
        if self.numpy:
            includes += "cimport numpy as np" + os.linesep
            includes += "import numpy as np" + os.linesep

        for t in self.stl.keys():
            if self.stl[t]:
                includes += ("from libcpp.%(type)s cimport %(type)s"
                             % {"type": t}) + os.linesep

        if self.deref:
            includes += ("from cython.operator cimport dereference as deref" +
                         os.linesep)
        includes += "cimport _declarations as cpp" + os.linesep
        return includes


class Enum:
    def __init__(self, filename, namespace, tipe):
        self.filename = filename
        self.namespace = namespace
        self.tipe = tipe
        self.constants = []

    def accept(self, exporter):
        exporter.visit_enum(self)

    def __str__(self):
        return "Enum '%s'" % self.tipe


class Typedef:
    def __init__(self, filename, namespace, tipe, underlying_type):
        self.filename = filename
        self.namespace = namespace
        self.tipe = tipe
        self.underlying_type = underlying_type

    def accept(self, exporter):
        exporter.visit_typedef(self)

    def __str__(self):
        return "Typedef (%s) %s" % (self.underlying_type, self.tipe)


class Clazz(object):
    def __init__(self, filename, namespace, name):
        self.filename = filename
        self.namespace = namespace
        self.name = name
        self.constructors = []
        self.methods = []
        self.fields = []

    def accept(self, exporter):
        for field in self.fields:
            field.accept(exporter)
        for ctor in self.constructors:
            ctor.accept(exporter)
        for method in self.methods:
            method.accept(exporter)
        exporter.visit_class(self)

    def __str__(self):
        result = "Class '%s'" % self.name
        if self.namespace != "":
            result += " (namespace: '%s')" % self.namespace
        if len(self.fields) > 0:
            result += os.linesep + indent_block(os.linesep.join(
                [str(field) for field in self.fields]), 1)
        if len(self.constructors) > 0:
            result += os.linesep + indent_block(os.linesep.join(
                [str(ctor) for ctor in self.constructors]), 1)
        if len(self.methods) > 0:
            result += os.linesep + indent_block(os.linesep.join(
                [str(method) for method in self.methods]), 1)
        return result


class FunctionBase(object):
    def __init__(self, name):
        self.name = name
        self.arguments = []
        self.ignored = False

    def accept(self, exporter):
        for arg in self.arguments:
            arg.accept(exporter)

    def __str__(self):
        result = "%s '%s'" % (self.__class__.__name__, self.name)
        if len(self.arguments) > 0:
            result += os.linesep + indent_block(os.linesep.join(
                [str(arg) for arg in self.arguments]), 1)
        return result


class Function(FunctionBase):
    def __init__(self, filename, namespace, name, result_type):
        super(Function, self).__init__(name)
        self.filename = filename
        self.namespace = namespace
        self.result_type = result_type

    def accept(self, exporter):
        super(Function, self).accept(exporter)
        exporter.visit_function(self)

    def __str__(self):
        result = super(Function, self).__str__()
        if self.result_type != "void":
            result += os.linesep + indent_block(
                "Returns (%s)" % self.result_type, 1)
        return result


class Constructor(FunctionBase):
    def __init__(self, class_name):
        super(Constructor, self).__init__("__init__")
        self.class_name = class_name

    def accept(self, exporter):
        super(Constructor, self).accept(exporter)
        exporter.visit_constructor(self)


class Method(FunctionBase):
    def __init__(self, name, result_type, class_name):
        super(Method, self).__init__(name)
        self.result_type = result_type
        self.class_name = class_name

    def accept(self, exporter):
        super(Method, self).accept(exporter)
        exporter.visit_method(self)

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
    def __init__(self, filename, namespace, name):
        Clazz.__init__(self, filename, namespace, name)
        Template.__init__(self)

    def accept(self, exporter):
        super(TemplateClass, self).accept(exporter)
        exporter.visit_template_class(self)

    def __str__(self):
        result = Clazz.__str__(self)
        result += os.linesep + Template.__str__(self)
        return result


class TemplateFunction(Function, Template):
    def __init__(self, filename, namespace, name, result_type):
        Function.__init__(self, filename, namespace, name, result_type)
        Template.__init__(self)

    def accept(self, exporter):
        super(Function, self).accept(exporter)
        exporter.visit_template_function(self)

    def __str__(self):
        result = Function.__str__(self)
        result += os.linesep + Template.__str__(self)
        return result


class TemplateMethod(Method, Template):
    def __init__(self, name, result_type, class_name):
        Method.__init__(self, name, result_type, class_name)
        Template.__init__(self)

    def accept(self, exporter):
        super(Method, self).accept(exporter)
        exporter.visit_template_method(self)

    def __str__(self):
        result = Method.__str__(self)
        result += os.linesep + Template.__str__(self)
        return result


class Param:
    def __init__(self, name, tipe):
        self.name = name
        self.tipe = tipe

    def accept(self, exporter):
        exporter.visit_param(self)

    def __str__(self):
        return "Parameter (%s) %s" % (self.tipe, self.name)


class Field:
    def __init__(self, name, tipe, class_name):
        self.name = name
        self.tipe = tipe
        self.class_name = class_name
        self.ignored = False

    def accept(self, exporter):
        exporter.visit_field(self)

    def __str__(self):
        return "Field (%s) %s" % (self.tipe, self.name)
