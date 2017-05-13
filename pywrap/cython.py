import os
import sys
from .defaultconfig import Config
from .exporter import CythonDeclarationExporter, CythonImplementationExporter
from .parser import Parser, Includes, TypeInfo
from .ast import postprocess_asts
from .templates import render
from .utils import (make_header, file_ending, hidden_stdout, hidden_stderr,
                    derive_module_name_from)


def load_config(custom_config):
    """Load configuration.

    Parameters
    ----------
    custom_config : str
        Name of the configuration file, must have the file ending ".py"
    """
    if custom_config is None:
        return Config()

    if not os.path.exists(custom_config):
        raise ValueError("Configuration file '%s' does not exist."
                         % custom_config)

    parts = custom_config.split(os.sep)
    path = os.sep.join(parts[:-1])
    filename = parts[-1]
    module = derive_module_name_from(filename)

    sys.path.insert(0, path)
    imported_module = __import__(module)
    sys.path.pop(0)
    return imported_module.config


def make_cython_wrapper(filenames, sources, modulename=None, target=".",
                        config=Config(), incdirs=(), compiler_flags=("-O3",),
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

    config : Config, optional (default: defaultconfig.Config())
        Configuration

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
        modulename = derive_module_name_from(filenames[0])
    if modulename is None:
        raise ValueError("Please give a module name when there are multiple "
                         "C++ files that you want to wrap.")

    for incdir in incdirs:
        if not os.path.exists(incdir):
            raise ValueError("Include directory '%s' does not exist." % incdir)

    for filename in filenames:
        if file_ending(filename) not in config.cpp_header_endings:
            raise ValueError("'%s' does not seem to be a header file which is "
                             "required." % filename)
        if not os.path.exists(filename):
            raise ValueError("File '%s' does not exist" % filename)

    includes, type_info, asts = _parse_files(
        filenames, config, incdirs, verbose)

    # TODO check if duplicates from separate modules are removed
    postprocess_asts(asts.values())

    extensions = _make_extension(asts, includes, type_info, config)
    declarations = _make_declarations(asts, includes, config)
    setup = _make_setup(sources, modulename, asts.keys(), target, incdirs,
                        compiler_flags, config)
    results = dict(extensions + declarations + [setup])

    if verbose >= 2:
        for filename in sorted(results.keys()):
            print(make_header("Exporting file '%s':" % filename))
            print(results[filename])

    return results


def _parse_files(filenames, config, incdirs, verbose):
    includes = Includes()
    type_info = TypeInfo(config)
    asts = {}
    for filename in filenames:
        modulename = derive_module_name_from(filename)
        parser = Parser(filename, includes, type_info, incdirs, verbose)
        asts[modulename] = parser.parse()
    return includes, type_info, asts


def _make_extension(asts, includes, type_info, config):
    cies = {}
    for modulename, ast in asts.iteritems():
        cie = CythonImplementationExporter(
            modulename, includes, type_info, config)
        type_info.enter_module(modulename)
        ast.accept(cie)
        type_info.exit_module()
        includes.add_custom_module(modulename)
        cies[modulename] = cie
    results = []
    for modulename, cie in cies.iteritems():
        pyx_filename = modulename + "." + config.pyx_file_ending
        body = cie.export()
        extension = includes.implementations_import() + body
        results.append((pyx_filename, extension))
    return results


def _make_declarations(asts, includes, config):
    cdes = {}
    for modulename, ast in asts.iteritems():
        cde = CythonDeclarationExporter(includes, config)
        ast.accept(cde)
        cdes[modulename] = cde
    results = []
    for modulename, cde in cdes.iteritems():
        pxd_filename = "_%s.%s" % (modulename, config.pxd_file_ending)
        body = cde.export()
        declarations = includes.declarations_import() + body
        for decl in config.additional_declarations:
            declarations += decl
        results.append((pxd_filename, declarations))
    return results


def _make_setup(sources, modulename, modules, target, incdirs, compiler_flags,
                config):
    sourcedir = os.path.relpath(".", start=target)
    source_relpaths = [os.path.relpath(filename, start=target)
                       for filename in sources]
    setup_py = render(
        "setup", filenames=source_relpaths, modulename=modulename,
        modules=modules, sourcedir=sourcedir, incdirs=incdirs,
        compiler_flags=compiler_flags, library_dirs=config.library_dirs,
        libraries=config.libraries)
    return "setup.py", setup_py


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


def run_setup(setuppy_name="setup.py", hide_errors=False):
    """Run setup script to build extension.

    Parameters
    ----------
    setuppy_name : str, optional (default: 'setup.py')
        Setup script name

    hide_errors : bool, optional (default: False)
        Hide output to stderr
    """
    cmd = "python %s build_ext --inplace" % setuppy_name
    with hidden_stdout():
        if hide_errors:
            with hidden_stderr():
                os.system(cmd)
        else:
            os.system(cmd)
