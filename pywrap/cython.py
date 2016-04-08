import os
try:
    from Cython.Build import cythonize
except:
    raise Exception("Install 'cython'.")
from .parser import parse
from . import defaultconfig as config
from .cpptypeconv import (is_type_with_automatic_conversion,
                          cython_define_basic_inputarg,
                          cython_define_nparray1d_inputarg)
from .utils import indent_block, from_camel_case
import warnings


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
        function_def = ConstructorDefinition(
            ctor.class_name, ctor.name, ctor.arguments, self.includes,
            initial_args=["self"]).make()
        self.ctors.append(indent_block(function_def, 1))

        self.arguments = []

    def visit_method(self, method):
        function_def = FunctionDefinition(
            method.name, method.arguments, self.includes, ["self"],
            method.result_type).make()
        self.methods.append(indent_block(function_def, 1))

        self.arguments = []

    def visit_param(self, param):
        self.arguments.append(config.py_arg_def % param.__dict__)

    def export(self):
        return self.includes.header() + os.linesep + os.linesep + self.output


class FunctionDefinition(object):
    def __init__(self, name, arguments, includes, initial_args, result_type):
        self.name = name
        self.arguments = arguments
        self.includes = includes
        self.initial_args = initial_args
        self.result_type = result_type

    def make(self):
        body, args, call_args = self._input_type_conversions(
            self.includes, self.initial_args)
        body += self._call_cpp_function(call_args, self.result_type)
        body += self._output_type_conversion(self.result_type)
        return self._signature(args) + os.linesep + indent_block(body, 1)

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


class ConstructorDefinition(FunctionDefinition):
    def __init__(self, class_name, name, arguments, includes, initial_args):
        super(ConstructorDefinition, self).__init__(
            name, arguments, includes, initial_args, result_type=None)
        self.class_name = class_name

    def _call_cpp_function(self, call_args, result_type):
        return "self.thisptr = new %s(%s)%s" % (
            self.class_name, ", ".join(call_args), os.linesep)

    def _signature(self, args):
        return "def __init__(%s):" % ", ".join(args)
