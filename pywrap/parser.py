try:
    import clang.cindex as ci
    ci.Config.set_library_path("/usr/lib/llvm-3.5/lib/")
except:
    raise Exception("Install 'python-clang-3.5' and 'libclang-3.5-dev'. "
                    "Note that a recent operating system is required, e.g. "
                    "Ubuntu 14.04.")
import os
import warnings
from .cpptypeconv import typename


def parse(include_file, parsable_file, module, verbose):
    index = ci.Index.create()
    translation_unit = index.parse(parsable_file)
    cursor = translation_unit.cursor

    ast = AST(module)
    ast.parse(cursor, parsable_file, include_file, verbose)
    return ast


class AST:
    """Abstract Syntax Tree."""
    def __init__(self, module):
        self.module = module
        self.namespace = ""
        self.last_function = None
        self.classes = []
        self.includes = Includes(module)

    def parse(self, node, parsable_file, include_file, verbose=0):
        namespace = self.namespace
        if verbose >= 2:
            print("Node: %s, %s" % (node.kind, node.displayname))

        if node.location.file is None:
            pass
        elif node.location.file.name != parsable_file:
            return
        elif node.kind == ci.CursorKind.NAMESPACE:
            if self.namespace == "":
                self.namespace = node.displayname
            else:
                self.namespace = self.namespace + "::" + node.displayname
        elif node.kind == ci.CursorKind.PARM_DECL:
            tname = typename(node.type.spelling)
            self.includes.add_include_for(tname)
            param = Param(node.displayname, tname)
            self.last_function.arguments.append(param)
        elif node.kind == ci.CursorKind.FUNCTION_DECL:
            warnings.warn("TODO functions are not implemented yet; name: '%s'"
                          % node.spelling)
        elif node.kind == ci.CursorKind.CXX_METHOD:
            tname = typename(node.result_type.spelling)
            self.includes.add_include_for(tname)
            method = Method(node.spelling, tname)
            self.classes[-1].methods.append(method)
            self.last_function = method
        elif node.kind == ci.CursorKind.CONSTRUCTOR:
            constructor = Constructor(node.spelling, self.classes[-1].name)
            self.classes[-1].constructors.append(constructor)
            self.last_function = constructor
        elif node.kind == ci.CursorKind.CLASS_DECL:
            clazz = Clazz(include_file, self.namespace, node.displayname)
            self.classes.append(clazz)
        else:
            if verbose:
                print("Unknown node: %s, %s" % (node.kind, node.displayname))

        for child in node.get_children():
            self.parse(child, parsable_file, include_file, verbose)

        self.namespace = namespace

    def accept(self, exporter):
        exporter.visit_ast(self)
        self.includes.accept(exporter)
        for clazz in self.classes:
            clazz.accept(exporter)


class Includes:
    def __init__(self, module):
        self.module = module
        self.numpy = False
        self.boolean = False
        self.vector = False
        self.string = False
        self.deref = False

    def add_include_for(self, tname):
        if tname == "bool" or self._part_of_tname(tname, "bool"):
            self.boolean = True
        elif tname == "string" or self._part_of_tname(tname, "string"):
            self.string = True
        elif tname == "vector" or self._part_of_tname(tname, "vector"):
            self.vector = True

    def add_include_for_deref(self):
        self.deref = True

    def _part_of_tname(self, tname, subtname):
        return (tname == subtname or ("<" + subtname + ">") in tname or
                tname.startswith(subtname))

    def header(self):
        includes = ""
        if self.numpy:
            includes += "cimport numpy as np" + os.linesep
            includes += "import numpy as np" + os.linesep
        if self.boolean:
            includes += "from libcpp cimport bool" + os.linesep
        if self.vector:
            includes += "from libcpp.vector cimport vector" + os.linesep
        if self.string:
            includes += "from libcpp.string cimport string" + os.linesep
        if self.deref:
            # TODO this is only required in the implementation
            includes += ("from cython.operator cimport dereference as deref" +
                         os.linesep)
        includes += "from _%s cimport *%s" % (self.module, os.linesep)
        return includes

    def accept(self, exporter):
        exporter.visit_includes(self)


class Clazz:
    def __init__(self, filename, namespace, name):
        self.filename = filename
        self.namespace = namespace
        self.name = name
        self.constructors = []
        self.methods = []

    def accept(self, exporter):
        for ctor in self.constructors:
            ctor.accept(exporter)
        for method in self.methods:
            method.accept(exporter)
        exporter.visit_class(self)


class FunctionBase(object):
    def __init__(self, name):
        self.name = name
        self.arguments = []

    def accept(self, exporter):
        for arg in self.arguments:
            arg.accept(exporter)


class Constructor(FunctionBase):
    def __init__(self, name, class_name):
        super(self.__class__, self).__init__(name)
        self.class_name = class_name

    def accept(self, exporter):
        super(Constructor, self).accept(exporter)
        exporter.visit_constructor(self)


class Method(FunctionBase):
    def __init__(self, name, result_type):
        super(self.__class__, self).__init__(name)
        self.result_type = result_type

    def accept(self, exporter):
        super(Method, self).accept(exporter)
        exporter.visit_method(self)


class Param:
    def __init__(self, name, tipe):
        self.name = name
        self.tipe = tipe

    def accept(self, exporter):
        exporter.visit_param(self)
