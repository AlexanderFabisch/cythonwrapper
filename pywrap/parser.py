from clang import cindex
cindex.Config.set_library_path("/usr/lib/llvm-3.5/lib/")
import warnings
from .type_conversion import cythontype_from_cpptype
from .ast import (AST, Enum, Typedef, Clazz, Function, Constructor, Method,
                  DummyFunction, Param, Field)


def parse(include_file, parsable_file, includes, verbose):
    index = cindex.Index.create()
    translation_unit = index.parse(parsable_file)
    cursor = translation_unit.cursor

    ast = AST(includes, include_file)
    convert_ast(ast, cursor, parsable_file, verbose)
    return ast


def convert_ast(ast, node, parsable_file, verbose=0):
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
    namespace = ast.namespace
    if verbose >= 2:
        print("Node: %s, %s" % (node.kind, node.displayname))

    parse_children = True
    try:
        if node.location.file is None:
            pass
        elif node.location.file.name != parsable_file:
            return
        elif node.kind == cindex.CursorKind.NAMESPACE:
            if ast.namespace == "":
                ast.namespace = node.displayname
            else:
                ast.namespace = ast.namespace + "::" + node.displayname
        elif node.kind == cindex.CursorKind.PARM_DECL:
            parse_children = add_param(ast, node.displayname,
                                       node.type.spelling)
        elif node.kind == cindex.CursorKind.FUNCTION_DECL:
            parse_children = add_function(ast, node.spelling,
                                          node.result_type.spelling)
        elif node.kind == cindex.CursorKind.FUNCTION_TEMPLATE:
            ast.last_function = DummyFunction()
            warnings.warn("Templates are not implemented yet")
        elif node.kind == cindex.CursorKind.CXX_METHOD:
            if node.access_specifier == cindex.AccessSpecifier.PUBLIC:
                parse_children = add_method(ast, node.spelling,
                                            node.result_type.spelling)
            else:
                parse_children = False
        elif node.kind == cindex.CursorKind.CONSTRUCTOR:
            if node.access_specifier == cindex.AccessSpecifier.PUBLIC:
                parse_children = add_ctor(ast)
            else:
                parse_children = False
        elif node.kind == cindex.CursorKind.CLASS_DECL:
            parse_children = add_class(ast, node.displayname)
        elif node.kind == cindex.CursorKind.STRUCT_DECL:
            parse_children = add_struct_decl(ast, node.displayname)
        elif node.kind == cindex.CursorKind.FIELD_DECL:
            if node.access_specifier == cindex.AccessSpecifier.PUBLIC:
                parse_children = add_field(ast, node.displayname,
                                           node.type.spelling)
            else:
                parse_children = False
        elif node.kind == cindex.CursorKind.TYPEDEF_DECL:
            tname = node.displayname
            parse_children = add_typedef(
                ast, node.underlying_typedef_type.spelling, tname)
        elif node.kind == cindex.CursorKind.ENUM_DECL:
            enum = Enum(ast.include_file, ast.namespace, node.displayname)
            ast.last_enum = enum
            ast.enums.append(enum)
        elif node.kind == cindex.CursorKind.ENUM_CONSTANT_DECL:
            ast.last_enum.constants.append(node.displayname)
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
            convert_ast(ast, child, parsable_file, verbose)

    ast.namespace = namespace


def add_typedef(ast, underlying_tname, tname):
    if underlying_tname == "struct " + tname:
        if ast.unnamed_struct is None:
            raise LookupError("Struct typedef does not match any "
                              "unnamed struct")
        ast.unnamed_struct.name = tname
        ast.classes.append(ast.unnamed_struct)
        ast.unnamed_struct = None
        ast.last_type = None
        return False
    else:
        ast.includes.add_include_for(underlying_tname)
        ast.typedefs.append(Typedef(
            ast.include_file, ast.namespace, tname,
            cythontype_from_cpptype(underlying_tname)))
        return True


def add_struct_decl(ast, name):
    if name == "" and ast.unnamed_struct is None:
        ast.unnamed_struct = Clazz(
            ast.include_file, ast.namespace, name)
        ast.last_type = ast.unnamed_struct
    else:
        add_class(ast, name)
    return True


def add_function(ast, name, tname):
    tname = cythontype_from_cpptype(tname)
    ast.includes.add_include_for(tname)
    function = Function(
        ast.include_file, ast.namespace, name, tname)
    ast.functions.append(function)
    ast.last_function = function
    return True


def add_class(ast, name):
    clazz = Clazz(ast.include_file, ast.namespace, name)
    ast.classes.append(clazz)
    ast.last_type = clazz
    return True


def add_ctor(ast):
    constructor = Constructor(ast.last_type.name)
    ast.last_type.constructors.append(constructor)
    ast.last_function = constructor
    return True


def add_method(ast, name, tname):
    tname = cythontype_from_cpptype(tname)
    ast.includes.add_include_for(tname)
    method = Method(name, tname, ast.last_type.name)
    ast.last_type.methods.append(method)
    ast.last_function = method
    return True


def add_param(ast, name, tname):
    tname = cythontype_from_cpptype(tname)
    ast.includes.add_include_for(tname)
    param = Param(name, tname)
    if ast.last_function is not None:
        ast.last_function.arguments.append(param)
    else:
        warnings.warn("Ignored function parameter '%s' (type: '%s'), no "
                      "function in current context." % (name, tname))
    return True


def add_field(ast, name, tname):
    tname = cythontype_from_cpptype(tname)
    ast.includes.add_include_for(tname)
    field = Field(name, tname, ast.last_type.name)
    ast.last_type.fields.append(field)
    return True