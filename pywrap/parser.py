from clang import cindex
cindex.Config.set_library_path("/usr/lib/llvm-3.5/lib/")
from .defaultconfig import Config
import warnings
import os
from .type_conversion import cythontype_from_cpptype
from .ast import (Ast, Enum, Typedef, Clazz, Function, TemplateClass,
                  TemplateFunction, Constructor, Method, TemplateMethod,
                  Param, Field)
from .utils import make_header


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


class TypeInfo:
    def __init__(self, config=Config(), typedefs=None):
        self.config = config
        self.classes = []
        self.typedefs = {}
        if typedefs is not None:
            self.typedefs.update(typedefs)
        self.enums = []
        self.spec = {}

    def attach_specialization(self, spec):
        self.spec = spec

    def remove_specialization(self):
        self.spec = {}

    def underlying_type(self, tname):
        while tname in self.typedefs or tname in self.spec:
            if tname in self.typedefs:
                tname = self.typedefs[tname]
            else:
                tname = self.spec[tname]
        return tname

    def get_specialization(self, tname):
        return self.spec.get(tname, tname)


IGNORED_NODES = [
    cindex.CursorKind.CALL_EXPR,
    cindex.CursorKind.CXX_ACCESS_SPEC_DECL,
    cindex.CursorKind.DECL_REF_EXPR,
    cindex.CursorKind.DECL_REF_EXPR,
    cindex.CursorKind.MEMBER_REF,
    cindex.CursorKind.NAMESPACE_REF,
    cindex.CursorKind.STRING_LITERAL,
    cindex.CursorKind.TEMPLATE_REF,
    cindex.CursorKind.TYPE_REF,
    cindex.CursorKind.UNEXPOSED_EXPR,
    cindex.CursorKind.CXX_BASE_SPECIFIER,
    cindex.CursorKind.DESTRUCTOR,
    cindex.CursorKind.VAR_DECL,
    cindex.CursorKind.UNEXPOSED_DECL,
]

LITERAL_NODES = {
    cindex.CursorKind.INTEGER_LITERAL:
        {
            "conversion": int,
            "typenames": ["short", "int", "long"]
        },
    cindex.CursorKind.FLOATING_LITERAL:
        {
            "conversion": float,
            "typenames": ["float", "double"]
        },
    cindex.CursorKind.CXX_BOOL_LITERAL_EXPR:
        {
            "conversion": lambda literal: literal == "true",
            "typenames": ["bool"]
        }
}


class Parser(object):
    """The parser builds the abstract syntax tree (AST).

    Parameters
    ----------
    include_file : str
        Name of the file that contains the declarations.

    parsable_file : str, optional
        File that will be parsed by clang. Clang does not really parse header
        files. In that case, we will copy the content to a .cc file and parse
        this file with clang.

    includes : Includes, optional
        Will be filled with information about required import and cimport
        statements.

    type_info : TypeInfo, optional
        Collects information about custom types.

    incdirs : list, optional
        Include directories that will be required to parse the file with clang.

    verbose : int, optional (default: 0)
        Verbosity level
    """
    def __init__(self, include_file, includes=Includes(), type_info=TypeInfo(),
                 incdirs=(), verbose=0):
        self.include_file = include_file
        self.includes = includes
        self.type_info = type_info
        self.incdirs = incdirs
        self.verbose = verbose

    def parse(self):
        """Parse the given file.

        Returns
        -------
        ast : Ast
            Abstract syntax tree that can be used to generate the Cython
            wrapper code
        """
        self._make_parsable_file()

        try:
            index = cindex.Index.create()
            incdirs = ["-I" + incdir for incdir in self.incdirs]
            translation_unit = index.parse(self.parsable_file, incdirs)
            cursor = translation_unit.cursor

            self.init_ast()
            if self.verbose >= 1:
                print(make_header("Parsing"))
            self.convert_ast(cursor, 0)
            if self.verbose >= 2:
                print(make_header("AST"))
                print(self.ast)
        finally:
            os.remove(self.parsable_file)

        return self.ast

    def _make_parsable_file(self):
        # Clang does not really parse headers
        self.parsable_file = self.include_file + ".cc"
        with open(self.parsable_file, "w") as outfile:
            with open(self.include_file, "r") as infile:
                outfile.write(infile.read())

    def init_ast(self):
        self.ast = Ast()
        self.last_type = None
        self.last_enum = None
        self.unnamed_struct = None
        self.last_function = None
        self.last_template = None
        self.last_param = None
        self.namespace = ""

    def convert_ast(self, node, depth):
        """Convert AST from Clang to our own representation.

        Parameters
        ----------
        node : clang.cindex.Index
            Currently visited node of Clang's AST

        depth : int
            Current depth in the AST
        """
        namespace = self.namespace
        if self.verbose >= 1:
            print("  " * depth + "Node: %s, %s" % (node.kind, node.displayname))

        parse_children = True
        class_added = False
        param_added = False
        try:
            if node.location.file is None:
                pass
            elif node.location.file.name != self.parsable_file:
                return
            elif node.kind == cindex.CursorKind.NAMESPACE:
                if self.namespace == "":
                    self.namespace = node.displayname
                else:
                    self.namespace = self.namespace + "::" + node.displayname
            elif node.kind == cindex.CursorKind.PARM_DECL:
                parse_children = self.add_param(
                    node.displayname, node.type.spelling)
                param_added = True
            elif node.kind == cindex.CursorKind.FUNCTION_DECL:
                parse_children = self.add_function(
                    node.spelling, node.result_type.spelling,
                    self.namespace)
            elif node.kind == cindex.CursorKind.CLASS_TEMPLATE:
                name = node.displayname.split("<")[0]
                self.add_template_class(name)
                class_added = True
            elif node.kind == cindex.CursorKind.FUNCTION_TEMPLATE:
                if self.last_type is None:
                    self.add_template_function(
                        node.spelling, node.result_type.spelling)
                else:
                    self.add_template_method(
                        node.spelling, node.result_type.spelling)
            elif node.kind == cindex.CursorKind.TEMPLATE_TYPE_PARAMETER:
                self.add_template_type(node.displayname)
            elif node.kind == cindex.CursorKind.CXX_METHOD:
                if node.access_specifier == cindex.AccessSpecifier.PUBLIC:
                    if node.is_static_method():
                        namespace = self.namespace
                        if namespace != "":
                            namespace += "::"
                        namespace += self.last_type.name
                        parse_children = self.add_function(
                            node.spelling, node.result_type.spelling,
                            namespace)
                    else:
                        parse_children = self.add_method(
                            node.spelling, node.result_type.spelling)
                else:
                    parse_children = False
            elif node.kind == cindex.CursorKind.CONSTRUCTOR:
                if node.access_specifier == cindex.AccessSpecifier.PUBLIC:
                    parse_children = self.add_ctor()
                else:
                    parse_children = False
            elif node.kind == cindex.CursorKind.CLASS_DECL:
                parse_children = self.add_class(node.displayname)
                class_added = True
            elif node.kind == cindex.CursorKind.STRUCT_DECL:
                parse_children = self.add_struct_decl(node.displayname)
            elif node.kind == cindex.CursorKind.FIELD_DECL:
                if node.access_specifier == cindex.AccessSpecifier.PUBLIC:
                    parse_children = self.add_field(
                        node.displayname, node.type.spelling)
                else:
                    parse_children = False
            elif node.kind == cindex.CursorKind.TYPEDEF_DECL:
                tname = node.displayname
                parse_children = self.add_typedef(
                    node.underlying_typedef_type.spelling, tname)
            elif node.kind == cindex.CursorKind.ENUM_DECL:
                parse_children = self.add_enum(node.displayname)
            elif node.kind == cindex.CursorKind.ENUM_CONSTANT_DECL:
                self.last_enum.constants.append(node.displayname)
            elif node.kind == cindex.CursorKind.COMPOUND_STMT:
                parse_children = False
            elif node.kind in LITERAL_NODES:
                literal_info = LITERAL_NODES[node.kind]
                if (self.last_param is not None and
                            self.last_param.tipe in literal_info["typenames"]):
                    tokens = list(node.get_tokens())
                    assert len(tokens) >= 1
                    value = literal_info["conversion"](tokens[0].spelling)
                    self.last_param.default_value = value
            elif node.kind == cindex.CursorKind.STRING_LITERAL:
                if (self.last_param is not None and
                            self.last_param.tipe == "string"):
                    self.last_param.default_value = node.displayname
            elif node.kind in IGNORED_NODES:
                if self.verbose >= 3:
                    print("  " * depth + "Ignored node: %s, %s"
                          % (node.kind, node.displayname))
            else:
                print("  " * depth + "Unknown node: %s, %s"
                      % (node.kind, node.displayname))
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring node '%s'" % node.displayname)
            parse_children = False

        if parse_children:
            for child in node.get_children():
                self.convert_ast(child, depth + 1)
        if class_added:
            self.last_type = None
        if param_added:
            self.last_param = None

        self.namespace = namespace

    def add_typedef(self, underlying_tname, tname):
        if underlying_tname == "struct " + tname:
            if self.ast.unnamed_struct is None:
                raise LookupError("Struct typedef does not match any "
                                  "unnamed struct")
            self.ast.unnamed_struct.name = tname
            self.ast.nodes.append(self.ast.unnamed_struct)
            self.type_info.classes.append(tname)
            self.ast.unnamed_struct = None
            self.last_type = None
            return False
        else:
            underlying_tname = cythontype_from_cpptype(underlying_tname)
            self.includes.add_include_for(underlying_tname)
            if self.last_type is None:
                namespace = self.namespace
            else:
                namespace = self.namespace + "::" + self.last_type.name
            typedef = Typedef(self.include_file, namespace, tname,
                              underlying_tname)
            self.ast.nodes.append(typedef)
            self.type_info.typedefs[tname] = underlying_tname
            return True

    def add_struct_decl(self, name):
        if name == "" and self.unnamed_struct is None:
            self.ast.unnamed_struct = Clazz(
                self.include_file, self.namespace, name)
            self.last_type = self.ast.unnamed_struct
        else:
            self.add_class(name)
        return True

    def add_enum(self, name):
        enum = Enum(self.include_file, self.namespace, name)
        self.type_info.enums.append(name)
        self.last_enum = enum
        self.ast.nodes.append(enum)
        return True

    def add_template_type(self, template_type):
        self.last_template.template_types.append(template_type)

    def add_function(self, name, tname, namespace):
        tname = cythontype_from_cpptype(tname)
        self.includes.add_include_for(tname)
        function = Function(
            self.include_file, namespace, name, tname)
        self.ast.nodes.append(function)
        self.last_function = function
        return True

    def add_template_function(self, name, tname):
        tname = cythontype_from_cpptype(tname)
        self.includes.add_include_for(tname)
        function = TemplateFunction(self.include_file, self.namespace, name,
                                    tname)
        self.ast.nodes.append(function)
        self.last_function = function
        self.last_template = function
        return True

    def add_class(self, name):
        clazz = Clazz(self.include_file, self.namespace, name)
        self.ast.nodes.append(clazz)
        self.last_type = clazz
        self.type_info.classes.append(name)
        return True

    def add_template_class(self, name):
        clazz = TemplateClass(self.include_file, self.namespace, name)
        self.ast.nodes.append(clazz)
        self.last_type = clazz
        self.last_template = clazz

        registered_specs = self.type_info.config.registered_template_specializations
        for key in registered_specs:
            if name == key:
                for spec_name, _ in registered_specs[key]:
                    self.type_info.classes.append(spec_name)
                break

        return True

    def add_ctor(self):
        constructor = Constructor(self.last_type.name)
        self.last_type.nodes.append(constructor)
        self.last_function = constructor
        return True

    def add_method(self, name, tname):
        tname = cythontype_from_cpptype(tname)
        self.includes.add_include_for(tname)
        method = Method(name, tname, self.last_type.name)
        self.last_type.nodes.append(method)
        self.last_function = method
        return True

    def add_template_method(self, name, tname):
        tname = cythontype_from_cpptype(tname)
        self.includes.add_include_for(tname)
        method = TemplateMethod(name, tname, self.last_type.name)
        self.last_type.nodes.append(method)
        self.last_function = method
        self.last_template = method
        return True

    def add_param(self, name, tname):
        tname = cythontype_from_cpptype(tname)
        self.includes.add_include_for(tname)
        param = Param(name, tname)
        self.last_param = param
        if self.last_function is not None:
            self.last_function.nodes.append(param)
        else:
            warnings.warn("Ignored function parameter '%s' (type: '%s'), no "
                          "function in current context." % (name, tname))
        return True

    def add_field(self, name, tname):
        tname = cythontype_from_cpptype(tname)
        self.includes.add_include_for(tname)
        field = Field(name, tname, self.last_type.name)
        self.last_type.nodes.append(field)
        return False
