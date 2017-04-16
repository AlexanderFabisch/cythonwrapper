import os
import glob
import clang
from clang import cindex


def _find_clang(verbose=0):
    """Find installation of libclang.

    python-clang does not know where to find libclang, so we have to do this
    here almost manually.
    """
    SUPPORTED_VERSIONS = ["3.8", "3.7", "3.6", "3.5"]
    # remove pythonX.Y/site-packages/clang/__init__.pyc from path
    basepath = os.sep.join(clang.__file__.split(os.sep)[:-4])

    if verbose >= 2:
        print("Found Python bindings of libclang in '%s'."
              % basepath)
    for clang_version in SUPPORTED_VERSIONS:
        search_paths = [
            # e.g. '/usr/lib' or '$HOME/anaconda3/envs/$ENV/lib'
            basepath,
            # e.g. '/usr/lib/llvm-3.8/lib'
            os.path.join(basepath, "llvm-%s" % clang_version, "lib")
        ]
        for lib_path in search_paths:
            if not os.path.exists(lib_path):
                continue
            if verbose >= 3:
                print("Searching for libclang in '%s'..." % lib_path)

            lib_names = ["libclang-%s.so" % clang_version,
                         "libclang.so.%s" % clang_version]
            lib_filename = None
            for lib_name in lib_names:
                lib_file = os.path.join(lib_path, lib_name)
                if os.path.exists(lib_file):
                    lib_filename = lib_file
                    break
            if verbose >= 3:
                if lib_filename is None:
                    print("No library found.")
                else:
                    print("Found libclang at '%s'." % lib_filename)
            if lib_filename is None:
                continue

            incdir_pattern = os.path.join(
                basepath, "clang/%s.?/include/" % clang_version)
            clang_incdirs = list(glob.glob(incdir_pattern))
            if len(clang_incdirs) != 1:
                raise ImportError(
                    "Could not find one clang include directory. "
                    "Checked '%s'." % incdir_pattern)
            clang_incdir = clang_incdirs[0]
            if verbose >= 3:
                print("Found clang include directory at '%s'."
                        % clang_incdir)

            cindex.Config.set_library_path(lib_path)

            return clang_version, clang_incdir
    raise ImportError("Could not find a valid installation of libclang-dev. "
                      "Only versions %s are supported at the moment."
                      % SUPPORTED_VERSIONS)


# This must be done globally and exactly once:
CLANG_VERSION, CLANG_INCDIR = _find_clang()
