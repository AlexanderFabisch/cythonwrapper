import os
import sys
from .templates import render
from .defaultconfig import Config
from .parser import Parser
from .ast import Includes
from .exporter import CythonDeclarationExporter, CythonImplementationExporter
from .utils import make_header


def write_files(files, target="."):
    """Write files.

    Parameters
    ----------
    files : dict
        Mapping from file name to content

    target : string, optional (default: '.')
        Target directory
    """
    for filename, content in files.items():
        outputfile = os.path.join(target, filename)
        with open(outputfile, "w") as f:
            f.write(content)


def make_cython_wrapper(filenames, sources, modulename=None, target=".",
                        custom_config=None, incdirs=[], compiler_flags=["-O3"],
                        verbose=0):
    """Make Cython wrapper for C++ files.

    Parameters
    ----------
    filenames : list of strings or string
        C++ files

    sources : list of strings
        C++ source files that have to be compiled

    modulename : string, optional (default: name of the only header)
        Name of the module

    target : string, optional (default: ".")
        Target directory

    incdirs : list, optional (default: [])
        Include directories

    compiler_flags : list, optional (default: ["-O3"])
        Flags that will be passed directly to the compiler when building the
        extension

    verbose : int, optional (default: 0)
        Verbosity level

    Returns
    -------
    results : dict
        Mapping from filename to generated file content
    """
    if isinstance(filenames, str):
        filenames = [filenames]
    if len(filenames) == 1 and modulename is None:
        modulename = _derive_module_name_from(filenames[0])
    if modulename is None:
        raise ValueError("Please give a module name when there are multiple "
                         "C++ files that you want to wrap.")

    for incdir in incdirs:
        if not os.path.exists(incdir):
            raise ValueError("Include directory '%s' does not exist." % incdir)

    config = _load_config(custom_config)

    for filename in filenames:
        if file_ending(filename) not in config.cpp_header_endings:
            raise ValueError("'%s' does not seem to be a header file which is "
                             "required." % filename)
        if not os.path.exists(filename):
            raise ValueError("File '%s' does not exist" % filename)

    includes = Includes()
    asts = _parse_files(filenames, includes, incdirs, verbose)
    type_info = TypeInfo(asts, config)

    results = dict(
        [_make_extension(modulename, asts, includes, type_info, config),
         _make_declarations(asts, includes, config),
         _make_setup(sources, modulename, target, incdirs, compiler_flags)]
    )

    if verbose >= 2:
        for filename in sorted(results.keys()):
            print(make_header("Exporting file '%s':" % filename))
            print(results[filename])

    return results


def _derive_module_name_from(filename):
    filename = filename.split(os.sep)[-1]
    return filename.split(".")[0]


def _load_config(custom_config):
    if custom_config is None:
        return Config()

    if not os.path.exists(custom_config):
        raise ValueError("Configuration file '%s' does not exist."
                         % custom_config)

    parts = custom_config.split(os.sep)
    path = os.sep.join(parts[:-1])
    filename = parts[-1]
    module = _derive_module_name_from(filename)

    sys.path.insert(0, path)
    m = __import__(module)
    sys.path.pop(0)
    return m.config


class TypeInfo:
    def __init__(self, asts=[], config=Config(), typedefs={}):
        self.classes = self._collect_classes(asts, config)
        self.typedefs = {typedef.tipe: typedef.underlying_type for ast in asts
                         for typedef in ast.typedefs}
        self.typedefs.update(typedefs)
        self.enums = [enum.tipe for ast in asts for enum in ast.enums]
        self.spec = {}

    def _collect_classes(self, asts, config):
        specializations = config.registered_template_specializations
        classes = []
        for ast in asts:
            for clazz in ast.classes:
                template = False
                for key in specializations:
                    if clazz.name == key:
                        template = True
                        for name, _ in specializations[key]:
                            classes.append(name)
                        break
                if not template:
                    classes.append(clazz.name)
        return classes

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


def _parse_files(filenames, includes, incdirs, verbose):
    asts = []
    for filename in filenames:
        # Clang does not really parse headers
        parsable_file = filename + ".cc"
        with open(parsable_file, "w") as outfile:
            with open(filename, "r") as infile:
                outfile.write(infile.read())

        try:
            asts.append(Parser(filename, parsable_file, includes, incdirs,
                               verbose).parse())
        finally:
            os.remove(parsable_file)

    return asts


def file_ending(filename):
    return filename.split(".")[-1]


def _make_extension(modulename, asts, includes, type_info, config):
    cie = CythonImplementationExporter(includes, type_info, config)
    for ast in asts:
        ast.accept(cie)
    pyx_filename = modulename + "." + config.pyx_file_ending
    extension = includes.implementations_import() + cie.export()
    return pyx_filename, extension


def _make_declarations(asts, includes, config):
    cde = CythonDeclarationExporter(includes, config)
    for ast in asts:
        ast.accept(cde)
    declarations = includes.declarations_import() + cde.export()
    for decl in config.additional_declerations:
        declarations += decl
    pxd_filename = "_declarations." + config.pxd_file_ending
    return pxd_filename, declarations


def _make_setup(sources, modulename, target, incdirs, compiler_flags):
    sourcedir = os.path.relpath(".", start=target)
    source_relpaths = [os.path.relpath(filename, start=target)
                       for filename in sources]
    return "setup.py", render("setup", filenames=source_relpaths,
                              module=modulename, sourcedir=sourcedir,
                              incdirs=incdirs, compiler_flags=compiler_flags)
