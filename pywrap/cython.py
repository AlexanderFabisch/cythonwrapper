import os
try:
    from Cython.Build import cythonize
except:
    raise Exception("Install 'cython'.")
from . import defaultconfig as config
from .parser import parse
from .exporter import CythonDeclarationExporter, CythonImplementationExporter


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
