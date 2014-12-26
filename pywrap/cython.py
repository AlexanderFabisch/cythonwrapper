import os
import warnings
try:
    import clang.cindex as ci
except:
    raise Exception("Install 'python-clang-3.5' and 'libclang-3.5-dev'")


CLASS_DEF = """cdef extern from "%(filename)s" namespace "%(namespace)s":
    cdef cppclass %(name)s:"""
METHOD_DEF = "        %(result_type)s %(name)s(%(args)s)"
CONSTRUCTOR_DEF = "        %(name)s(%(args)s)"
ARG_DEF = "%(tipe)s %(name)s"

PY_CLASS_DEF = """cdef class Cpp%(name)s:
    cdef %(name)s *thisptr

    def __dealloc__(self):
        del self.thisptr
"""
PY_ARG_DEF = "%(name)s"
SETUP_PY = """import os


def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration
    import numpy

    config = Configuration('.', parent_package, top_path)

    config.add_extension(
        '%(module)s',
        sources=["%(module)s.cpp", "%(filename)s"], #created by cython
        include_dirs=[".", numpy.get_include()],
        define_macros=[("NDEBUG",)],
        extra_compile_args=["-O3"],
        language="c++",
    )
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
"""


def write_cython_wrapper(filename, verbose=0):
    results, cython_files = make_cython_wrapper(filename, verbose)
    for filename, content in results.items():
        open(filename, "w").write(content)
    for cython_file in cython_files:
        os.system("cython --cplus %s" % cython_file)


def make_cython_wrapper(filename, verbose=0):
    results = {}

    parts = filename.split(".")
    module = ".".join(parts[:-1])

    pxd_filename = "_" + module + ".pxd"
    pyx_filename = module + ".pyx"

    tmpfile = filename
    header = parts[-1] in ["h", "hh", "hpp"]

    if header:
        tmpfile = filename + ".cc"
        with open(tmpfile, "w") as f:
            f.write(open(filename, "r").read())

    state = parse(tmpfile, module, verbose)

    output = state.to_pxd()
    if header:
        output = output.replace(tmpfile, filename)
        os.remove(tmpfile)
    results[pxd_filename] = output
    if verbose >= 2:
        print("= %s =" % pxd_filename)
        print(output)

    output = state.to_pyx()
    results[pyx_filename] = output
    if verbose >= 2:
        print("= %s =" % pyx_filename)
        print(output)

    setup = make_setup(filename=filename, module=module)
    results["setup.py"] = setup

    # Files that will be cythonized
    cython_files = [pyx_filename]

    return results, cython_files


def make_setup(**kwargs):
    return SETUP_PY % kwargs


def parse(filename, module, verbose):
    index = ci.Index.create()
    translation_unit = index.parse(filename)
    cursor = translation_unit.cursor

    state = State(module)
    recurse(cursor, filename, state, verbose)
    return state


class State:
    def __init__(self, module):
        self.module = module
        self.namespace = ""
        self.last_function = None
        self.classes = []

    def to_pxd(self):
        return "\n".join(map(to_pxd, self.classes))

    def to_pyx(self):
        includes = Includes(self.module)
        code = "\n".join([clazz.to_pyx(includes) for clazz in self.classes])
        return includes.to_pyx() + os.linesep + os.linesep + code


class Includes:
    def __init__(self, module):
        self.module = module
        self.numpy = False
        self.boolean = False
        self.vector = False
        self.string = False

    def to_pyx(self):
        includes = ""
        if self.numpy:
            includes += """cimport numpy as np
import numpy as np""" + os.linesep
        if self.boolean:
            includes += "" + os.linesep  # TODO
        if self.vector:
            includes += "" + os.linesep  # TODO
        if self.string:
            includes += "from libcpp.string cimport string" + os.linesep
        #includes += "cimport _" + self.module + os.linesep
        includes += "from _%s cimport *%s" % (self.module, os.linesep)
        return includes


class Clazz:
    def __init__(self, filename, namespace, name):
        self.filename = filename
        self.namespace = namespace
        self.name = name
        self.constructors = []
        self.methods = []

    def to_pxd(self):
        class_str = CLASS_DEF % self.__dict__
        consts_str = os.linesep.join(map(to_pxd, self.constructors))
        methods_str = os.linesep.join(map(to_pxd, self.methods))
        return class_str + os.linesep + consts_str + os.linesep + methods_str

    def to_pyx(self, includes):
        if len(self.constructors) > 1:
            msg = ("Class '%s' has more than one constructor. This is not "
                   "compatible to Python. The last constructor will overwrite "
                   "all others." % self.name)
            warnings.warn(msg)
        class_str = PY_CLASS_DEF % self.__dict__
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
        method_str = METHOD_DEF % method_dict
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
        const_str = CONSTRUCTOR_DEF % const_dict
        return const_str

    def to_pyx(self, includes):
        return function_def(self.name, self.arguments, includes,
                            constructor=True, class_name=self.class_name)


def function_def(function, arguments, includes, constructor=False, **kwargs):
    ind = "        "
    body = ""
    call_args = []
    args = []
    skip = False
    for i in range(len(arguments)):
        if skip:
            skip = False
            continue

        argument = arguments[i]
        cppname = "cpp_" + argument.name

        args.append(argument.name)
        call_args.append(cppname)

        if argument.tipe in ["int", "float", "double"]:
            body += "%scdef %s %s = %s%s" % (ind, argument.tipe, cppname,
                                             argument.name, os.linesep)
        if argument.tipe == "bool":
            includes.boolean = True
            # TODO
        elif argument.tipe == "double *":
            includes.numpy = True
            body += "%scdef np.ndarray[double, ndim=1] %s_array = np.asarray(%s)%s" % (ind, argument.name, argument.name, os.linesep)
            body += "%scdef %s %s = &%s_array[0]%s" % (ind, argument.tipe, cppname, argument.name, os.linesep)
            call_args.append(argument.name + "_array.shape[0]")
            skip = True

    if constructor:
        body += "%sself.thisptr = new %s(%s)%s" % (ind, kwargs["class_name"], ", ".join(call_args), os.linesep)
    elif kwargs["result_type"] == "void":
        body += "%sself.thisptr.%s(%s)%s" % (ind, function, ", ".join(call_args), os.linesep)
    else:
        body += "%scdef %s result = self.thisptr.%s(%s)%s" % (ind, kwargs["result_type"], function, ", ".join(call_args), os.linesep)
        body += "%sreturn result%s" % (ind, os.linesep)

    if constructor:
        signature = "    def __cinit__(self, %s):" % ", ".join(args)
    else:
        signature = "    def %s(self, %s):" % (function, ", ".join(args))

    return signature + os.linesep + body


class Param:
    def __init__(self, name, tipe):
        self.name = name
        self.tipe = tipe

    def to_pxd(self):
        return ARG_DEF % self.__dict__

    def to_pyx(self):
        return PY_ARG_DEF % self.__dict__


def recurse(node, filename, state, verbose=0):
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
        param = Param(node.displayname, typename(node.type.spelling))
        state.last_function.arguments.append(param)
    elif node.kind == ci.CursorKind.CXX_METHOD:
        method = Method(node.spelling, typename(node.result_type.spelling))
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
        recurse(child, filename, state, verbose)

    state.namespace = namespace


def from_camel_case(name):
    new_name = str(name)
    i = 0
    while i < len(new_name):
        if new_name[i].isupper():
            new_name = new_name[:i] + "_" + new_name[i:]
            i += 1
        i += 1
    return new_name.lower()


def typename(name):
    # TODO does not work with std::vector<namespace::type>
    # Remove const modifier
    new_name = name.replace("const ", "")
    # Remove namespace
    return new_name.split("::")[-1]


def to_pxd(obj):
    return obj.to_pxd()


def to_pyx(obj):
    return obj.to_pyx()
