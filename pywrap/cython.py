import os
import sys
from .templates import render
from .defaultconfig import Config
from .parser import Parser
from .ast import Includes
from .exporter import CythonDeclarationExporter, CythonImplementationExporter


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


def cython(cython_files, target="."):
    """Cythonize Cython implementation files.

    Parameters
    ----------
    cython_files : list
        List of files that will be cythonized

    target : string, optional (default: '.')
        Target directory
    """
    for cython_file in cython_files:
        inputfile = os.path.join(target, cython_file)
        #from Cython.Build import cythonize
        #cythonize(inputfile, cplus=True)
        os.system("cython --cplus %s" % inputfile)


def make_cython_wrapper(filenames, sources, modulename=None, target=".",
                        custom_config=None, verbose=0):
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

    verbose : int, optional (default: 0)
        Verbosity level

    Returns
    -------
    results : dict
        Mapping from filename to generated file content

    files_to_cythonize : list
        Files that we have to convert with Cython
    """
    if isinstance(filenames, str):
        filenames = [filenames]
    if len(filenames) == 1 and modulename is None:
        modulename = _derive_module_name_from(filenames[0])
    if modulename is None:
        raise ValueError("Please give a module name when there are multiple "
                         "C++ files that you want to wrap.")

    config = _load_config(custom_config)

    for filename in filenames:
        if not os.path.exists(filename):
            raise ValueError("File '%s' does not exist" % filename)
        if file_ending(filename) not in config.cpp_header_endings:
            raise ValueError("'%s' does not seem to be a header file which is "
                             "required.")

    includes = Includes()
    asts = _parse_files(filenames, includes, config, verbose)
    type_info = TypeInfo(asts)

    ext_results, files_to_cythonize = _generate_extension(
        modulename, asts, includes, type_info, config, verbose)
    decl_results = _generate_declarations(asts, includes, config, verbose)

    results = {}
    results.update(ext_results)
    results.update(decl_results)
    results["setup.py"] = _make_setup(sources, modulename, target)

    return results, files_to_cythonize


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
    def __init__(self, asts):
        self.classes = [clazz.name for ast in asts for clazz in ast.classes]
        self.typedefs = {typedef.tipe: typedef.underlying_type for ast in asts
                         for typedef in ast.typedefs}
        self.enums = [enum.tipe for ast in asts for enum in ast.enums]


def _parse_files(filenames, includes, config, verbose):
    asts = []
    for filename in filenames:
        # Clang does not really parse headers
        parsable_file = filename + ".cc"
        with open(parsable_file, "w") as outfile:
            with open(filename, "r") as infile:
                outfile.write(infile.read())

        try:
            asts.append(Parser(filename, parsable_file, includes, verbose).parse())
        finally:
            os.remove(parsable_file)

    return asts


def file_ending(filename):
    return filename.split(".")[-1]


def _generate_extension(modulename, asts, includes, type_info, config, verbose):
    results = {}
    files_to_cythonize = []
    extension = ""
    for ast in asts:
        cie = CythonImplementationExporter(includes, type_info, config)
        ast.accept(cie)
        extension += cie.export()
    pyx_filename = modulename + "." + config.pyx_file_ending
    results[pyx_filename] = includes.implementations_import() + extension
    files_to_cythonize.append(pyx_filename)
    if verbose >= 2:
        print("= %s =" % pyx_filename)
        print(extension)
    return results, files_to_cythonize


def _generate_declarations(asts, includes, config, verbose):
    results = {}
    declarations = ""
    for ast in asts:
        cde = CythonDeclarationExporter(includes, config)
        ast.accept(cde)
        declarations += cde.export()
    pxd_filename = "_declarations." + config.pxd_file_ending
    results[pxd_filename] = includes.declarations_import() + declarations
    if verbose >= 2:
        print("= %s =" % pxd_filename)
        print(declarations)
    return results


def _make_setup(sources, modulename, target):
    sourcedir = os.path.relpath(".", start=target)
    source_relpaths = [os.path.relpath(filename, start=target)
                       for filename in sources]
    return render("setup", filenames=source_relpaths,
                  module=modulename, sourcedir=sourcedir)
