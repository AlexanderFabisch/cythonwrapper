from clang import cindex
cindex.Config.set_library_path("/usr/lib/llvm-3.5/lib/")
import warnings
from .type_conversion import cythontype_from_cpptype
from .ast import (AST, Enum, Typedef, Clazz, Function, TemplateClass,
                  TemplateFunction, Constructor, Method, TemplateMethod,
                  Param, Field)
from .utils import make_header


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
    cindex.CursorKind.UNEXPOSED_EXPR
]


class Parser(object):
    def __init__(self, include_file, parsable_file, includes, verbose=0):
        self.include_file = include_file
        self.parsable_file = parsable_file
        self.includes = includes
        self.verbose = verbose

    def parse(self):
        index = cindex.Index.create()
        translation_unit = index.parse(self.parsable_file)
        cursor = translation_unit.cursor

        self.init_ast()
        if self.verbose >= 1:
            print(make_header("Parsing"))
        self.convert_ast(cursor)
        return self.ast

    def init_ast(self):
        self.ast = AST()
        self.last_type = None
        self.last_enum = None
        self.unnamed_struct = None
        self.last_function = None
        self.last_template = None
        self.namespace = ""

    def convert_ast(self, node):
        """Convert AST from Clang to our own representation.

        Parameters
        ----------
        node : clang.cindex.Index
            Currently visited node of Clang's AST
        """
        namespace = self.namespace
        if self.verbose >= 1:
            print("Node: %s, %s" % (node.kind, node.displayname))

        parse_children = True
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
            elif node.kind == cindex.CursorKind.FUNCTION_DECL:
                parse_children = self.add_function(
                    node.spelling, node.result_type.spelling,
                    self.namespace)
            elif node.kind == cindex.CursorKind.CLASS_TEMPLATE:
                name = node.displayname.split("<")[0]
                self.add_template_class(name)
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
                enum = Enum(self.include_file, self.namespace, node.displayname)
                self.last_enum = enum
                self.ast.enums.append(enum)
            elif node.kind == cindex.CursorKind.ENUM_CONSTANT_DECL:
                self.last_enum.constants.append(node.displayname)
            elif node.kind == cindex.CursorKind.COMPOUND_STMT:
                parse_children = False
            elif node.kind in IGNORED_NODES:
                if self.verbose >= 3:
                    print("Ignored node: %s, %s"
                          % (node.kind, node.displayname))
            else:
                print("Unknown node: %s, %s"
                      % (node.kind, node.displayname))
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring node '%s'" % node.displayname)
            parse_children = False

        if parse_children:
            for child in node.get_children():
                self.convert_ast(child)

        self.namespace = namespace

    def add_typedef(self, underlying_tname, tname):
        if underlying_tname == "struct " + tname:
            if self.ast.unnamed_struct is None:
                raise LookupError("Struct typedef does not match any "
                                  "unnamed struct")
            self.ast.unnamed_struct.name = tname
            self.ast.classes.append(self.ast.unnamed_struct)
            self.ast.unnamed_struct = None
            self.last_type = None
            return False
        else:
            self.includes.add_include_for(underlying_tname)
            self.ast.typedefs.append(Typedef(
                self.include_file, self.namespace, tname,
                cythontype_from_cpptype(underlying_tname)))
            return True

    def add_struct_decl(self, name):
        if name == "" and self.unnamed_struct is None:
            self.ast.unnamed_struct = Clazz(
                self.include_file, self.namespace, name)
            self.last_type = self.ast.unnamed_struct
        else:
            self.add_class(name)
        return True

    def add_template_type(self, template_type):
        self.last_template.template_types.append(template_type)

    def add_function(self, name, tname, namespace):
        tname = cythontype_from_cpptype(tname)
        self.includes.add_include_for(tname)
        function = Function(
            self.include_file, namespace, name, tname)
        self.ast.functions.append(function)
        self.last_function = function
        return True

    def add_template_function(self, name, tname):
        tname = cythontype_from_cpptype(tname)
        self.includes.add_include_for(tname)
        function = TemplateFunction(self.include_file, self.namespace, name,
                                    tname)
        self.ast.functions.append(function)
        self.last_function = function
        self.last_template = function
        return True

    def add_class(self, name):
        clazz = Clazz(self.include_file, self.namespace, name)
        self.ast.classes.append(clazz)
        self.last_type = clazz
        return True

    def add_template_class(self, name):
        clazz = TemplateClass(self.include_file, self.namespace, name)
        self.ast.classes.append(clazz)
        self.last_type = clazz
        self.last_template = clazz
        return True

    def add_ctor(self):
        constructor = Constructor(self.last_type.name)
        self.last_type.constructors.append(constructor)
        self.last_function = constructor
        return True

    def add_method(self, name, tname):
        tname = cythontype_from_cpptype(tname)
        self.includes.add_include_for(tname)
        method = Method(name, tname, self.last_type.name)
        self.last_type.methods.append(method)
        self.last_function = method
        return True

    def add_template_method(self, name, tname):
        tname = cythontype_from_cpptype(tname)
        self.includes.add_include_for(tname)
        method = TemplateMethod(name, tname, self.last_type.name)
        self.last_type.methods.append(method)
        self.last_function = method
        self.last_template = method
        return True

    def add_param(self, name, tname):
        tname = cythontype_from_cpptype(tname)
        self.includes.add_include_for(tname)
        param = Param(name, tname)
        if self.last_function is not None:
            self.last_function.arguments.append(param)
        else:
            warnings.warn("Ignored function parameter '%s' (type: '%s'), no "
                          "function in current context." % (name, tname))
        return True

    def add_field(self, name, tname):
        tname = cythontype_from_cpptype(tname)
        self.includes.add_include_for(tname)
        field = Field(name, tname, self.last_type.name)
        self.last_type.fields.append(field)
        return True
