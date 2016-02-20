import os
import warnings
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
from .cpptypeconv import (is_basic_type, is_type_with_automatic_conversion,
                          typename, cython_define_basic_inputarg,
                          cython_define_nparray1d_inputarg)


ci.Config.set_library_path("/usr/lib/llvm-3.5/lib/")


def write_cython_wrapper(filename, target=".", verbose=0):
    if not os.path.exists(target):
        os.makedirs(target)

    results, cython_files = make_cython_wrapper(filename, target, verbose)
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


def make_cython_wrapper(filename, target=".", verbose=0):
    results = {}

    module = _derive_module_name_from(filename)

    pxd_filename = "_" + module + "." + config.pxd_file_ending
    pyx_filename = module + "." + config.pyx_file_ending

    header = _file_ending(filename) in config.cpp_header_endings

    tmpfile = filename

    if header:
        tmpfile = filename + ".cc"
        with open(tmpfile, "w") as f:
            f.write(open(filename, "r").read())

    state = parse(tmpfile, module, verbose)

    extension = state.to_pyx()
    results[pyx_filename] = extension
    if verbose >= 2:
        print("= %s =" % pyx_filename)
        print(extension)

    declarations = state.to_pxd()
    if header:
        relpath = os.path.relpath(filename, start=target)
        declarations = declarations.replace(tmpfile, relpath)
        os.remove(tmpfile)
    results[pxd_filename] = declarations

    if verbose >= 2:
        print("= %s =" % pxd_filename)
        print(declarations)

    sourcedir = os.path.relpath(".", start=target)
    setup = make_setup(filename=relpath, module=module, sourcedir=sourcedir)
    results["setup.py"] = setup

    # Files that will be cythonized
    cython_files = [pyx_filename]

    return results, cython_files


def _file_ending(filename):
    return filename.split(".")[-1]


def _derive_module_name_from(filename):
    filename = filename.split(os.sep)[-1]
    return filename.split(".")[0]


def make_setup(**kwargs):
    return config.setup_py % kwargs


def parse(filename, module, verbose):
    index = ci.Index.create()
    translation_unit = index.parse(filename)
    cursor = translation_unit.cursor

    state = State(module)
    state.parse(cursor, filename, state, verbose)
    return state


class State:
    def __init__(self, module):
        self.module = module
        self.namespace = ""
        self.last_function = None
        self.classes = []
        self.includes = Includes(module)

    def parse(self, node, filename, state, verbose=0):
        namespace = state.namespace
        if verbose >= 2:
            print("Node: %s, %s" % (node.kind, node.displayname))

        if node.location.file is None:
            pass
        elif node.location.file.name != filename:
            return
        elif node.kind == ci.CursorKind.NAMESPACE:
            if state.namespace == "":
                state.namespace = node.displayname
            else:
                state.namespace = state.namespace + "::" + node.displayname
        elif node.kind == ci.CursorKind.PARM_DECL:
            tname = typename(node.type.spelling)
            state.includes.add_include_for(tname)
            param = Param(node.displayname, tname)
            state.last_function.arguments.append(param)
        elif node.kind == ci.CursorKind.FUNCTION_DECL:
            raise NotImplementedError("TODO functions are not implemented yet")
        elif node.kind == ci.CursorKind.CXX_METHOD:
            tname = typename(node.result_type.spelling)
            state.includes.add_include_for(tname)
            method = Method(node.spelling, tname)
            state.classes[-1].methods.append(method)
            state.last_function = method
        elif node.kind == ci.CursorKind.CONSTRUCTOR:
            constructor = Constructor(node.spelling, state.classes[-1].name)
            state.classes[-1].constructors.append(constructor)
            state.last_function = constructor
        elif node.kind == ci.CursorKind.CLASS_DECL:
            clazz = Clazz(filename, state.namespace, node.displayname)
            state.classes.append(clazz)
        else:
            if verbose:
                print("Unknown node: %s, %s" % (node.kind, node.displayname))

        for child in node.get_children():
            self.parse(child, filename, state, verbose)

        state.namespace = namespace

    def to_pxd(self):
        return self.includes.to_pxd() + "\n".join(map(to_pxd, self.classes))

    def to_pyx(self):
        code = "\n".join([clazz.to_pyx(self.includes) for clazz in self.classes])
        return self.includes.to_pyx() + os.linesep + os.linesep + code


class Includes:
    def __init__(self, module):
        self.module = module
        self.numpy = False
        self.boolean = False
        self.vector = False
        self.string = False

    def add_include_for(self, tname):
        if tname == "bool":
            self.boolean = True
        elif tname == "string":
            self.string = True

    def _header(self):
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

    def to_pxd(self):
        return self._header()

    def to_pyx(self):
        return self._header()


class Clazz:
    def __init__(self, filename, namespace, name):
        self.filename = filename
        self.namespace = namespace
        self.name = name
        self.constructors = []
        self.methods = []

    def to_pxd(self):
        class_str = config.class_def % self.__dict__

        if len(self.constructors) == 0 and len(self.methods) == 0:
            return class_str + os.linesep

        consts_str = os.linesep.join(map(to_pxd, self.constructors))
        methods_str = os.linesep.join(map(to_pxd, self.methods))
        return class_str + os.linesep + consts_str + os.linesep + methods_str

    def to_pyx(self, includes):
        if len(self.constructors) > 1:
            msg = ("Class '%s' has more than one constructor. This is not "
                   "compatible to Python. The last constructor will overwrite "
                   "all others." % self.name)
            warnings.warn(msg)
        class_str = config.py_class_def % self.__dict__
        consts_str = os.linesep.join([const.to_pyx(includes) for const in self.constructors])
        methods_str = os.linesep.join([method.to_pyx(includes) for method in self.methods])
        return class_str + os.linesep + consts_str + os.linesep + methods_str


class Method:
    def __init__(self, name, result_type):
        self.name = name
        self.arguments = []
        self.result_type = result_type

    def to_pxd(self):
        method_dict = {"args": ", ".join(map(to_pxd, self.arguments))}
        method_dict.update(self.__dict__)
        method_str = config.method_def % method_dict
        return method_str

    def to_pyx(self, includes):
        return function_def(self.name, self.arguments, includes,
                            constructor=False, result_type=self.result_type)


class Constructor:
    def __init__(self, name, class_name):
        self.name = name
        self.class_name = class_name
        self.arguments = []

    def to_pxd(self):
        const_dict = {"args": ", ".join(map(to_pxd, self.arguments))}
        const_dict.update(self.__dict__)
        const_str = config.constructor_def % const_dict
        return const_str

    def to_pyx(self, includes):
        return function_def(self.name, self.arguments, includes,
                            constructor=True, class_name=self.class_name)


def function_def(function, arguments, includes, constructor=False,
                 result_type="void", class_name=None):
    if class_name is None and constructor:
        raise ValueError("Constructurs require a class name.")

    ind = "        "
    body = ""
    call_args = []
    args = ["self"]
    skip = False
    for i in range(len(arguments)):
        if skip:
            skip = False
            continue

        argument = arguments[i]
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

    if constructor:
        body += "%sself.thisptr = new %s(%s)%s" % (ind, class_name, ", ".join(call_args), os.linesep)
    else:
        body += _call_cpp_function(result_type, function, call_args)

        if result_type == "void":
            pass
        elif is_type_with_automatic_conversion(result_type):
            body += "%sreturn result%s" % (ind, os.linesep)
        else:
            # TODO only works with default constructor
            cython_classname = "Cpp%s" % result_type.split()[0]
            body += """%sret = %s()
        ret.thisptr = result
        return ret%s""" % (ind, cython_classname, os.linesep)

    if constructor:
        signature = "    def __init__(%s):" % ", ".join(args)
    else:
        signature = "    def %s(%s):" % (from_camel_case(function), ", ".join(args))

    return signature + os.linesep + body


def _call_cpp_function(result_tname, fname, call_args):
    call = "self.thisptr.{fname}({args})".format(fname=fname,
                                                 args=", ".join(call_args))
    if result_tname != "void":
        call = "cdef {result_tname} result = {call}".format(
            result_tname=result_tname, call=call)
    return "    " * 2 + call + os.linesep


class Param:
    def __init__(self, name, tipe):
        self.name = name
        self.tipe = tipe

    def to_pxd(self):
        return config.arg_def % self.__dict__

    def to_pyx(self):
        return config.py_arg_def % self.__dict__


def from_camel_case(name):
    new_name = str(name)
    i = 0
    while i < len(new_name):
        if new_name[i].isupper():
            new_name = new_name[:i] + "_" + new_name[i:]
            i += 1
        i += 1
    return new_name.lower()


def to_pxd(obj):
    return obj.to_pxd()


def to_pyx(obj):
    return obj.to_pyx()
