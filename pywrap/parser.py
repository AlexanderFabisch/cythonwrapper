from clang import cindex
cindex.Config.set_library_path("/usr/lib/llvm-3.5/lib/")
import warnings
from .type_conversion import cythontype_from_cpptype
from .ast import (AST, Enum, Typedef, Clazz, Function, Constructor, Method,
                  DummyFunction, Param, Field)


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
        self.convert_ast(cursor, self.parsable_file, self.verbose)
        return self.ast

    def init_ast(self):
        self.ast = AST(self.includes, self.include_file)

    def convert_ast(self, node, parsable_file, verbose=0):
        """Convert AST from Clang to our own representation.

        Parameters
        ----------
        ast : AST
            Our abstract syntax tree (result)

        node : clang.cindex.Index
            Currently visited node of Clang's AST

        parsable_file : string
            Name of the file that is actually parsed by Clang

        verbose : int, optional (default: 0)
            Verbosity level
        """
        namespace = self.ast.namespace
        if verbose >= 2:
            print("Node: %s, %s" % (node.kind, node.displayname))

        parse_children = True
        try:
            if node.location.file is None:
                pass
            elif node.location.file.name != parsable_file:
                return
            elif node.kind == cindex.CursorKind.NAMESPACE:
                if self.ast.namespace == "":
                    self.ast.namespace = node.displayname
                else:
                    self.ast.namespace = self.ast.namespace + "::" + node.displayname
            elif node.kind == cindex.CursorKind.PARM_DECL:
                parse_children = self.add_param(
                    node.displayname, node.type.spelling)
            elif node.kind == cindex.CursorKind.FUNCTION_DECL:
                parse_children = self.add_function(
                    node.spelling, node.result_type.spelling)
            elif node.kind == cindex.CursorKind.FUNCTION_TEMPLATE:
                self.ast.last_function = DummyFunction()
                warnings.warn("Templates are not implemented yet")
            elif node.kind == cindex.CursorKind.CXX_METHOD:
                if node.access_specifier == cindex.AccessSpecifier.PUBLIC:
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
                enum = Enum(self.ast.include_file, self.ast.namespace, node.displayname)
                self.ast.last_enum = enum
                self.ast.enums.append(enum)
            elif node.kind == cindex.CursorKind.ENUM_CONSTANT_DECL:
                self.ast.last_enum.constants.append(node.displayname)
            elif node.kind == cindex.CursorKind.COMPOUND_STMT:
                parse_children = False
            else:
                if verbose:
                    print("Ignored node: %s, %s" % (node.kind, node.displayname))
        except NotImplementedError as e:
            warnings.warn(e.message + " Ignoring node '%s'" % node.displayname)
            parse_children = False

        if parse_children:
            for child in node.get_children():
                self.convert_ast(child, parsable_file, verbose)

        self.ast.namespace = namespace


    def add_typedef(self, underlying_tname, tname):
        if underlying_tname == "struct " + tname:
            if self.ast.unnamed_struct is None:
                raise LookupError("Struct typedef does not match any "
                                  "unnamed struct")
            self.ast.unnamed_struct.name = tname
            self.ast.classes.append(self.ast.unnamed_struct)
            self.ast.unnamed_struct = None
            self.ast.last_type = None
            return False
        else:
            self.ast.includes.add_include_for(underlying_tname)
            self.ast.typedefs.append(Typedef(
                self.ast.include_file, self.ast.namespace, tname,
                cythontype_from_cpptype(underlying_tname)))
            return True


    def add_struct_decl(self, name):
        if name == "" and self.ast.unnamed_struct is None:
            self.ast.unnamed_struct = Clazz(
                self.ast.include_file, self.ast.namespace, name)
            self.ast.last_type = self.ast.unnamed_struct
        else:
            self.add_class(name)
        return True


    def add_function(self, name, tname):
        tname = cythontype_from_cpptype(tname)
        self.ast.includes.add_include_for(tname)
        function = Function(
            self.ast.include_file, self.ast.namespace, name, tname)
        self.ast.functions.append(function)
        self.ast.last_function = function
        return True


    def add_class(self, name):
        clazz = Clazz(self.ast.include_file, self.ast.namespace, name)
        self.ast.classes.append(clazz)
        self.ast.last_type = clazz
        return True


    def add_ctor(self):
        constructor = Constructor(self.ast.last_type.name)
        self.ast.last_type.constructors.append(constructor)
        self.ast.last_function = constructor
        return True


    def add_method(self, name, tname):
        tname = cythontype_from_cpptype(tname)
        self.ast.includes.add_include_for(tname)
        method = Method(name, tname, self.ast.last_type.name)
        self.ast.last_type.methods.append(method)
        self.ast.last_function = method
        return True


    def add_param(self, name, tname):
        tname = cythontype_from_cpptype(tname)
        self.ast.includes.add_include_for(tname)
        param = Param(name, tname)
        if self.ast.last_function is not None:
            self.ast.last_function.arguments.append(param)
        else:
            warnings.warn("Ignored function parameter '%s' (type: '%s'), no "
                          "function in current context." % (name, tname))
        return True


    def add_field(self, name, tname):
        tname = cythontype_from_cpptype(tname)
        self.ast.includes.add_include_for(tname)
        field = Field(name, tname, self.ast.last_type.name)
        self.ast.last_type.fields.append(field)
        return True
