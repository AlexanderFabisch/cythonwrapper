import os

try:
    import clang.cindex as ci
except:
    raise Exception("Install 'python-clang-3.5' and 'libclang-3.5-dev'. "
                    "Note that a recent operating system is required, e.g. "
                    "Ubuntu 14.04.")
try:
    from Cython.Build import cythonize
except:
    raise Exception("Install 'cython'.")
from . import defaultconfig as config
from .cpptypeconv import (is_type_with_automatic_conversion, typename,
                          cython_define_basic_inputarg,
                          cython_define_nparray1d_inputarg)
from .utils import indent_block, from_camel_case
import warnings


ci.Config.set_library_path("/usr/lib/llvm-3.5/lib/")


def write_cython_wrapper(filenames, target=".", verbose=0):
    if not os.path.exists(target):
        os.makedirs(target)

    results, cython_files = make_cython_wrapper(filenames, target, verbose)
    write_files(results, target)
    cython(cython_files, target)


def write_files(files, target="."):
    for filename, content in files.items():
        outputfile = os.path.join(target, filename)
        open(outputfile, "w").write(content)


def cython(cython_files, target="."):
    for cython_file in cython_files:
        inputfile = os.path.join(target, cython_file)
        #cythonize(inputfile, cplus=True)
        os.system("cython --cplus %s" % inputfile)


def make_cython_wrapper(filenames, target=".", verbose=0):
    if isinstance(filenames, str):
        filenames = [filenames]

    asts = _parse_files(filenames, verbose)

    results = {}
    files_to_cythonize = []
    for module, ast in asts.items():
        cie = CythonImplementationExporter()
        ast.accept(cie)
        extension = cie.export()
        pyx_filename = module + "." + config.pyx_file_ending
        results[pyx_filename] = extension
        files_to_cythonize.append(pyx_filename)
        if verbose >= 2:
            print("= %s =" % pyx_filename)
            print(extension)

        cde = CythonDeclarationExporter()
        ast.accept(cde)
        declarations = cde.export()
        pxd_filename = "_" + module + "." + config.pxd_file_ending
        results[pxd_filename] = declarations
        if verbose >= 2:
            print("= %s =" % pxd_filename)
            print(declarations)

    results["setup.py"] = _make_setup(filenames, target)

    return results, files_to_cythonize


def _parse_files(filenames, verbose):
    asts = {}
    extensions_setup = []
    for filename in filenames:
        module = _derive_module_name_from(filename)
        is_header = _file_ending(filename) in config.cpp_header_endings

        if is_header:  # Clang does not really parse headers
            parsable_file = filename + ".cc"
            with open(parsable_file, "w") as f:  # TODO look for cp in os
                f.write(open(filename, "r").read())
        else:
            parsable_file = filename

        asts[module] = parse(filename, parsable_file, module, verbose)

        if is_header:
            os.remove(parsable_file)

    return asts


def _make_setup(filenames, target):
    sourcedir = os.path.relpath(".", start=target)
    extensions_setup = []
    for filename in filenames:
        module = _derive_module_name_from(filename)
        header_relpath = os.path.relpath(filename, start=target)
        extensions_setup.append(make_extension(
            filename=header_relpath, module=module, sourcedir=sourcedir))
    return config.setup_py % {"extensions": "".join(extensions_setup)}


def _derive_module_name_from(filename):
    filename = filename.split(os.sep)[-1]
    return filename.split(".")[0]


def _file_ending(filename):
    return filename.split(".")[-1]


def make_extension(**kwargs):
    return config.setup_extension % kwargs


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

    def add_include_for(self, tname):
        if tname == "bool" or self._part_of_tname(tname, "bool"):
            self.boolean = True
        elif tname == "string" or self._part_of_tname(tname, "string"):
            self.string = True
        elif tname == "vector" or self._part_of_tname(tname, "vector"):
            self.vector = True

    def _part_of_tname(self, tname, subtname):
        return (tname == subtname or ("<" + subtname + ">") in tname
                or tname.startswith(subtname))

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

    def function_def(self, includes, initial_args=[], result_type=None):
        body, args, call_args = self._input_type_conversions(
            includes, initial_args)
        body += self._call_cpp_function(call_args, result_type)
        body += self._output_type_conversion(result_type)
        return self._signature(args) + os.linesep + indent_block(body, 1)

    def accept(self, exporter):
        for arg in self.arguments:
            arg.accept(exporter)

    def _call_cpp_function(self, call_args, result_type=None):
        call = "self.thisptr.{fname}({args})".format(
            fname=self.name, args=", ".join(call_args))
        if result_type != "void":
            call = "cdef {result_type} result = {call}".format(
                result_type=result_type, call=call)
        return call + os.linesep

    def _signature(self, args):
        return "def %s(%s):" % (from_camel_case(self.name), ", ".join(args))

    def _input_type_conversions(self, includes, initial_args):
        body = ""
        call_args = []
        args = []
        args.extend(initial_args)
        skip = False

        for i in range(len(self.arguments)):
            if skip:
                skip = False
                continue

            argument = self.arguments[i]
            cppname = "cpp_" + argument.name

            args.append(argument.name)
            call_args.append(cppname)

            if is_type_with_automatic_conversion(argument.tipe):
                body += cython_define_basic_inputarg(
                    argument.tipe, cppname, argument.name) + os.linesep
            elif argument.tipe == "double *":
                includes.numpy = True
                body += cython_define_nparray1d_inputarg(
                    argument.tipe, cppname, argument.name)
                call_args.append(argument.name + "_array.shape[0]")
                skip = True
            elif argument.tipe.startswith("vector"):
                body += cython_define_basic_inputarg(
                    argument.tipe, cppname, argument.name) + os.linesep
            else:
                raise NotImplementedError("No known conversion for type %r"
                                          % argument.tipe)

        return body, args, call_args

    def _output_type_conversion(self, result_type):
        if result_type is None or result_type == "void":
            return ""
        elif is_type_with_automatic_conversion(result_type):
            return "return result" + os.linesep
        else:
            # TODO only works with default constructor
            cython_classname = "Cpp%s" % result_type.split()[0]
            return """ret = %s()
ret.thisptr = result
return ret
""" % cython_classname


class Constructor(FunctionBase):
    def __init__(self, name, class_name):
        super(self.__class__, self).__init__(name)
        self.class_name = class_name

    def _call_cpp_function(self, call_args, result_type):
        return "self.thisptr = new %s(%s)%s" % (
            self.class_name, ", ".join(call_args), os.linesep)

    def _signature(self, args):
        return "def __init__(%s):" % ", ".join(args)

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


class CythonDeclarationExporter:
    """Export AST to Cython declaration file (.pxd).

    This class implements the visitor pattern.
    """
    def __init__(self):
        self.output = ""
        self.ctors = []
        self.methods = []
        self.arguments = []

    def visit_ast(self, ast):
        pass

    def visit_includes(self, includes):
        self.output += includes.header()

    def visit_class(self, clazz):
        class_str = config.class_def % clazz.__dict__

        self.output += (os.linesep + class_str
                        + os.linesep + os.linesep.join(self.ctors)
                        + os.linesep + os.linesep.join(self.methods))

        self.ctors = []
        self.methods = []

    def visit_constructor(self, ctor):
        const_dict = {"args": ", ".join(self.arguments)}
        const_dict.update(ctor.__dict__)
        const_str = config.constructor_def % const_dict
        self.ctors.append(const_str)

        self.arguments = []

    def visit_method(self, method):
        method_dict = {"args": ", ".join(self.arguments)}
        method_dict.update(method.__dict__)
        method_str = config.method_def % method_dict
        self.methods.append(method_str)

        self.arguments = []

    def visit_param(self, param):
        self.arguments.append(config.arg_def % param.__dict__)

    def export(self):
        return self.output


class CythonImplementationExporter:
    """Export AST to Cython implementation file (.pyx).

    This class implements the visitor pattern.
    """
    def __init__(self):
        self.output = ""
        self.ctors = []
        self.methods = []
        self.arguments = []

    def visit_ast(self, ast):
        pass

    def visit_includes(self, includes):
        self.includes = includes

    def visit_class(self, clazz):
        if len(self.ctors) > 1:
            msg = ("Class '%s' has more than one constructor. This is not "
                   "compatible to Python. The last constructor will overwrite "
                   "all others." % clazz.name)
            warnings.warn(msg)
        class_str = config.py_class_def % clazz.__dict__
        self.output += (os.linesep + os.linesep + class_str
                        + os.linesep + os.linesep.join(self.ctors)
                        + os.linesep + os.linesep.join(self.methods))

        self.ctors = []
        self.methods = []

    def visit_constructor(self, ctor):
        const_str = indent_block(
            ctor.function_def(self.includes, initial_args=["self"]), 1)
        self.ctors.append(const_str)

        self.arguments = []

    def visit_method(self, method):
        method_str = indent_block(method.function_def(
            self.includes, initial_args=["self"],
            result_type=method.result_type), 1)
        self.methods.append(method_str)

        self.arguments = []

    def visit_param(self, param):
        self.arguments.append(config.py_arg_def % param.__dict__)

    def export(self):
        return self.includes.header() + os.linesep + os.linesep + self.output
