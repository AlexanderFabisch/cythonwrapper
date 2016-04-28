import os


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


class Typedef:
    def __init__(self, filename, namespace, tipe, underlying_type):
        self.filename = filename
        self.namespace = namespace
        self.tipe = tipe
        self.underlying_type = underlying_type

    def accept(self, exporter):
        exporter.visit_typedef(self)


class Clazz:
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


class FunctionBase(object):
    def __init__(self, name):
        self.name = name
        self.arguments = []
        self.ignored = False

    def accept(self, exporter):
        for arg in self.arguments:
            arg.accept(exporter)


class Function(FunctionBase):
    def __init__(self, filename, namespace, name, result_type):
        super(self.__class__, self).__init__(name)
        self.filename = filename
        self.namespace = namespace
        self.result_type = result_type

    def accept(self, exporter):
        super(Function, self).accept(exporter)
        exporter.visit_function(self)


class Constructor(FunctionBase):
    def __init__(self, class_name):
        super(self.__class__, self).__init__(None)
        self.class_name = class_name

    def accept(self, exporter):
        super(Constructor, self).accept(exporter)
        exporter.visit_constructor(self)


class Method(FunctionBase):
    def __init__(self, name, result_type, class_name):
        super(self.__class__, self).__init__(name)
        self.result_type = result_type
        self.class_name = class_name

    def accept(self, exporter):
        super(Method, self).accept(exporter)
        exporter.visit_method(self)


class DummyFunction(FunctionBase):
    def __init__(self):
        super(DummyFunction, self).__init__("")


class Param:
    def __init__(self, name, tipe):
        self.name = name
        self.tipe = tipe

    def accept(self, exporter):
        exporter.visit_param(self)


class Field:
    def __init__(self, name, tipe, class_name):
        self.name = name
        self.tipe = tipe
        self.class_name = class_name
        self.ignored = False

    def accept(self, exporter):
        exporter.visit_field(self)